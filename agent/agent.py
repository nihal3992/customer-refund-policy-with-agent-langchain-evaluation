from datetime import date

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import InMemorySaver

from agent.models import build_model
from agent.objects import Answer
from agent.prompts import agent_system_prompt
from agent.tools import build_tools


def build_agent(*, model: BaseChatModel | None = None, as_of: date | None = None):
    """Create isolated model and conversation state without import-time API calls."""
    return create_agent(
        model=model if model is not None else build_model(),
        tools=build_tools(as_of=as_of),
        system_prompt=agent_system_prompt,
        checkpointer=InMemorySaver(),
        response_format=Answer,
    )
