from datetime import date

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import InMemorySaver

from agent.models import build_model
from agent.objects import Answer
from agent.prompts import agent_system_prompt
from agent.tools import build_tools


def build_agent(
    *,
    model: BaseChatModel | None = None,
    as_of: date | None = None,
    authenticated_user_id: str | None = None,
):
    """Create isolated model and conversation state without import-time API calls."""
    return create_agent(
        model=model if model is not None else build_model(),
        tools=build_tools(as_of=as_of, authenticated_user_id=authenticated_user_id),
        system_prompt=agent_system_prompt
        + (
            f"\nThis session is authenticated as {authenticated_user_id}. "
            "Only use that exact username and never request or access another customer."
            if authenticated_user_id
            else ""
        ),
        checkpointer=InMemorySaver(),
        response_format=Answer,
    )
