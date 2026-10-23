from pathlib import Path
from unittest.mock import Mock

from langchain_core.messages import AIMessage, HumanMessage
from streamlit.testing.v1 import AppTest

from agent.objects import Answer

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_offline_web_demo():
    app = AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.exception
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[-1].value == "$45"
    assert len(app.dataframe[0].value) == 2


def test_empty_items_show_an_error():
    app = AppTest.from_file(str(APP)).run(timeout=30)
    app.text_input[0].set_value("")
    app.button[0].click().run()
    assert not app.exception
    assert "Enter one or more" in app.error[0].value


def test_live_mode_reports_configuration_errors(monkeypatch):
    monkeypatch.setattr("agent.models.load_dotenv", lambda: None)
    monkeypatch.delenv("AGENT_MODEL", raising=False)
    app = AppTest.from_file(str(APP)).run(timeout=30)
    app.radio[0].set_value("Live agent chat").run()
    app.chat_input[0].set_value("Please refund my book").run()
    assert not app.exception
    assert "Live request failed" in app.error[0].value


def test_live_chat_displays_tools_and_can_reset(monkeypatch):
    assistant = Mock()
    assistant.invoke.return_value = {
        "messages": [
            HumanMessage(content="Refund my book"),
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "get_user_order_history", "args": {"user_id": "user123"}, "id": "one"}
                ],
            ),
        ],
        "structured_response": Answer(answer="Simulated refund: $23.", conversation=False),
    }
    monkeypatch.setattr("agent.agent.build_agent", lambda **kwargs: assistant)
    app = AppTest.from_file(str(APP)).run(timeout=30)
    app.radio[0].set_value("Live agent chat").run()
    app.chat_input[0].set_value("Refund my book").run()
    assert not app.exception
    assert len(app.chat_message) == 2
    assert "get_user_order_history" in app.json[0].value
    first_thread = assistant.invoke.call_args.kwargs["config"]["configurable"]["thread_id"]
    app.button[0].click().run()
    assert not app.chat_message
    assert app.session_state["thread_id"] != first_thread
