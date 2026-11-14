import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agent.agent import build_agent
from agent.data import users_data
from agent.policy import DEMO_DATE, RefundQuote, quote_refund
from agent.tools import TOOL_NAMES
from api.auth import (
    AuthenticatedUser,
    clear_session,
    create_session,
    current_user,
    verify_demo_credentials,
)
from api.models import (
    ChatRequest,
    ChatResponse,
    LoginRequest,
    OrderResponse,
    QuoteRequest,
    SessionResponse,
    TicketRequest,
    TicketResponse,
    ToolTrace,
)

logger = logging.getLogger(__name__)
app = FastAPI(
    title="Refund Lab API",
    version="1.0.0",
    description="Deterministic refund policy and inspectable agent demo.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.assistants = {}


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=SessionResponse)
def login(payload: LoginRequest, response: Response) -> SessionResponse:
    if not verify_demo_credentials(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The demo username or password is incorrect",
        )
    create_session(response, payload.username)
    return SessionResponse(username=payload.username)


@app.get("/api/auth/session", response_model=SessionResponse)
def session(user: AuthenticatedUser = Depends(current_user)) -> SessionResponse:
    return SessionResponse(username=user.username)


@app.delete("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    clear_session(response)


@app.get("/api/orders", response_model=list[OrderResponse])
def orders(user: AuthenticatedUser = Depends(current_user)) -> list[OrderResponse]:
    result = []
    for name, order in users_data[user.username].items():
        line = quote_refund(user.username, [name], as_of=DEMO_DATE).items[0]
        result.append(
            OrderResponse(
                name=name,
                price=order["price"],
                purchase_date=order["date"],
                reason=line.reason,
                refundable=line.reason == "eligible",
            )
        )
    return result


@app.post("/api/refunds/quote", response_model=RefundQuote)
def refund_quote(
    payload: QuoteRequest, user: AuthenticatedUser = Depends(current_user)
) -> RefundQuote:
    try:
        return quote_refund(user.username, payload.items, as_of=DEMO_DATE)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error


@app.post("/api/refunds/tickets", response_model=TicketResponse)
def create_ticket(
    payload: TicketRequest, user: AuthenticatedUser = Depends(current_user)
) -> TicketResponse:
    quote = quote_refund(user.username, payload.items, as_of=DEMO_DATE)
    if quote.amount <= 0 or payload.refund_amount != quote.amount:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Refund amount no longer matches the policy quote",
                "expected_amount": quote.amount,
            },
        )
    return TicketResponse(
        status="success",
        ticket_id=f"RFD-{uuid4().hex[:8].upper()}",
        amount=quote.amount,
        created_at=datetime.now(timezone.utc).isoformat(),
        quote=quote,
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, user: AuthenticatedUser = Depends(current_user)) -> ChatResponse:
    key = (user.username, payload.conversation_id)
    try:
        assistant = app.state.assistants.get(key)
        if assistant is None:
            assistant = build_agent(as_of=DEMO_DATE, authenticated_user_id=user.username)
            app.state.assistants[key] = assistant
        response = assistant.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"Authenticated customer: {user.username}. "
                            f"Customer message: {payload.message}"
                        ),
                    }
                ]
            },
            config={"configurable": {"thread_id": payload.conversation_id}},
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except Exception as error:
        logger.exception("Agent request failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The configured model could not complete this request",
        ) from error

    traces = [
        ToolTrace(name=call["name"], arguments=call["args"])
        for message in response["messages"]
        for call in getattr(message, "tool_calls", [])
        if call["name"] in TOOL_NAMES
    ]
    answer = response["structured_response"]
    return ChatResponse(answer=answer.answer, conversation=answer.conversation, tools=traces)


FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/{path:path}", include_in_schema=False)
def frontend(path: str):
    index = FRONTEND_DIST / "index.html"
    requested = FRONTEND_DIST / path
    if path and requested.is_file() and FRONTEND_DIST in requested.resolve().parents:
        return FileResponse(requested)
    if index.is_file():
        return FileResponse(index)
    return {"name": "Refund Lab API", "docs": "/docs"}
