from typing import Literal

from pydantic import BaseModel, Field

from agent.policy import RefundQuote


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class SessionResponse(BaseModel):
    username: str
    demo: bool = True


class OrderResponse(BaseModel):
    name: str
    price: int
    purchase_date: str
    reason: Literal["eligible", "future purchase", "outside 30-day window"]
    refundable: bool


class QuoteRequest(BaseModel):
    items: list[str] = Field(min_length=1)


class TicketRequest(QuoteRequest):
    refund_amount: int = Field(gt=0)


class TicketResponse(BaseModel):
    status: Literal["success"]
    ticket_id: str
    amount: int
    simulated: bool = True
    created_at: str
    quote: RefundQuote


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)
    conversation_id: str = Field(min_length=8, max_length=100)


class ToolTrace(BaseModel):
    name: str
    arguments: dict


class ChatResponse(BaseModel):
    answer: str
    conversation: bool
    tools: list[ToolTrace]
