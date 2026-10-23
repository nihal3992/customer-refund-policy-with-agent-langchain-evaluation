import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel


def build_model() -> BaseChatModel:
    load_dotenv()
    model_name = os.getenv("AGENT_MODEL")
    if not model_name:
        raise ValueError("Set AGENT_MODEL in .env before starting live chat. See README.md.")
    provider = os.getenv("AGENT_MODEL_PROVIDER")
    return init_chat_model(model=model_name, model_provider=provider, temperature=0)
