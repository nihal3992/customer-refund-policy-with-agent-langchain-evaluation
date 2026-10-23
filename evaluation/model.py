import os

from dotenv import load_dotenv


def evaluator_model() -> str:
    load_dotenv()
    name = os.getenv("EVAL_MODEL")
    if not name:
        raise ValueError("Set EVAL_MODEL for the DeepEval judge. See README.md.")
    return name
