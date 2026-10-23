from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from agent.agent import build_agent
from agent.policy import DEMO_DATE


class ScriptedModel(BaseChatModel):
    responses: list[AIMessage]

    @property
    def _llm_type(self) -> str:
        return "offline-scripted-test"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs: Any) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=self.responses.pop(0))])


def call(name, args, identifier):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": identifier}])


def test_real_graph_executes_tools_and_returns_structured_answer():
    items = [{"name": "book"}]
    args = {"user_id": "user123", "item_name": items}
    model = ScriptedModel(
        responses=[
            call("get_user_order_history", {"user_id": "user123"}, "history"),
            call("get_today_date", {}, "date"),
            call("calculate_right_refund_amount", args, "amount"),
            call("issue_refund_ticket", {**args, "refund_amount": 23}, "ticket"),
            call(
                "Answer",
                {"answer": "Simulated ticket issued for $23.", "conversation": False},
                "end",
            ),
        ]
    )
    agent = build_agent(model=model, as_of=DEMO_DATE)
    config = {"configurable": {"thread_id": "test"}}
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "Refund my book. I am user123."}]},
        config=config,
    )
    assert response["structured_response"].conversation is False
    assert "$23" in response["structured_response"].answer
    ticket = next(
        message
        for message in response["messages"]
        if message.type == "tool" and message.name == "issue_refund_ticket"
    )
    assert '"simulated": true' in ticket.content
    assert len(agent.get_state(config).values["messages"]) > 1
    assert not agent.get_state({"configurable": {"thread_id": "other"}}).values


def test_model_configuration_is_lazy_and_explicit(monkeypatch):
    from agent.models import build_model

    monkeypatch.setattr("agent.models.load_dotenv", lambda: None)
    monkeypatch.delenv("AGENT_MODEL", raising=False)
    import pytest

    with pytest.raises(ValueError, match="AGENT_MODEL"):
        build_model()
