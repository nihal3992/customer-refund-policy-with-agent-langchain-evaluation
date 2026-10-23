import json
import subprocess
import sys
from unittest.mock import Mock

from agent.models import build_model


def test_cli_demo_without_model_credentials():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent.cli",
            "--demo",
            "--user",
            "user123",
            "--items",
            "book",
            "pen",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    banner, payload = result.stdout.split("\n", 1)
    assert "no LLM" in banner
    assert json.loads(payload)["amount"] == 30


def test_model_factory_uses_selected_provider(monkeypatch):
    monkeypatch.setattr("agent.models.load_dotenv", lambda: None)
    monkeypatch.setenv("AGENT_MODEL", "custom-model")
    monkeypatch.setenv("AGENT_MODEL_PROVIDER", "custom-provider")
    factory = Mock()
    monkeypatch.setattr("agent.models.init_chat_model", factory)
    assert build_model() is factory.return_value
    factory.assert_called_once_with(
        model="custom-model", model_provider="custom-provider", temperature=0
    )
