import argparse
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import uuid4

from deepeval import evaluate
from deepeval.dataset import Golden
from deepeval.evaluate import CacheConfig, DisplayConfig
from deepeval.integrations.langchain import CallbackHandler
from deepeval.metrics import (
    ArgumentCorrectnessMetric,
    GEval,
    PlanAdherenceMetric,
    PlanQualityMetric,
    StepEfficiencyMetric,
    TaskCompletionMetric,
    ToolCorrectnessMetric,
)
from deepeval.metrics.base_metric import BaseMetric
from deepeval.test_case import LLMTestCase, SingleTurnParams, ToolCall

from agent.agent import build_agent
from agent.policy import DEMO_DATE
from agent.tools import TOOL_NAMES
from evaluation.dataset import dataset
from evaluation.model import evaluator_model

SUCCESSFUL_TASK_DESCRIPTION = """
Ask for a username when missing. Verify the customer and requested purchases.
Only refund requested, owned items with purchase ages between 0 and 30 days,
inclusive. Explain expired, future, and unowned items. Never issue a ticket for
an unknown customer or a zero refund. For mixed eligibility, refund only eligible
items. For information-only requests, give purchase information without a ticket.
Report the simulated ticket status accurately; never claim a real payment occurred.
"""

METRIC_NAMES = (
    "task_completion",
    "step_efficiency",
    "plan_quality",
    "plan_adherence",
    "argument_correctness",
    "tool_correctness",
    "answer_correctness",
)


def build_metrics(selected: str = "all") -> tuple[list[BaseMetric], list[BaseMetric]]:
    if selected != "all" and selected not in METRIC_NAMES:
        raise ValueError(f"Unknown metric: {selected}")
    model = evaluator_model()
    trace_factories = {
        "task_completion": lambda: TaskCompletionMetric(
            threshold=0.8, model=model, task=SUCCESSFUL_TASK_DESCRIPTION, include_reason=True
        ),
        "step_efficiency": lambda: StepEfficiencyMetric(threshold=0.8, model=model),
        "plan_quality": lambda: PlanQualityMetric(threshold=0.8, model=model),
        "plan_adherence": lambda: PlanAdherenceMetric(threshold=0.8, model=model),
    }
    single_factories = {
        "argument_correctness": lambda: ArgumentCorrectnessMetric(threshold=0.8, model=model),
        "tool_correctness": lambda: ToolCorrectnessMetric(
            threshold=0.8, model=model, should_consider_ordering=True
        ),
        "answer_correctness": lambda: GEval(
            name="Answer Correctness",
            evaluation_params=[
                SingleTurnParams.INPUT,
                SingleTurnParams.ACTUAL_OUTPUT,
                SingleTurnParams.EXPECTED_OUTPUT,
            ],
            evaluation_steps=[
                "Compare the response with the reference in the context of the request.",
                "Check approval or denial, refund amount, and eligible or excluded items.",
                "Penalize unsupported claims about issuing tickets or transferring money.",
                "Ignore wording differences when the outcome is equivalent.",
            ],
            threshold=0.8,
            model=model,
        ),
    }
    return (
        [factory() for name, factory in trace_factories.items() if selected in ("all", name)],
        [factory() for name, factory in single_factories.items() if selected in ("all", name)],
    )


def make_test_case(golden: Golden, response: Mapping[str, Any]) -> LLMTestCase:
    tools = [
        ToolCall(name=call["name"], input_parameters=call["args"])
        for message in response["messages"]
        for call in getattr(message, "tool_calls", [])
        if call["name"] in TOOL_NAMES
    ]
    return LLMTestCase(
        input=golden.input,
        expected_output=golden.expected_output,
        actual_output=response["structured_response"].answer,
        tools_called=tools,
        expected_tools=golden.expected_tools,
    )


def run(selected: str = "all") -> None:
    trace_metrics, single_turn_metrics = build_metrics(selected)
    agent = build_agent(as_of=DEMO_DATE)
    cache = CacheConfig(use_cache=False, write_cache=False)
    display = DisplayConfig(inspect_after_run=False)
    goldens = (
        dataset.evals_iterator(metrics=trace_metrics, cache_config=cache, display_config=display)
        if trace_metrics
        else dataset.goldens
    )
    test_cases = []
    for golden in goldens:
        response = agent.invoke(
            {"messages": [{"role": "user", "content": golden.input}]},
            config={
                "configurable": {"thread_id": str(uuid4())},
                "callbacks": [CallbackHandler()] if trace_metrics else [],
            },
        )
        test_cases.append(make_test_case(golden, response))
    if single_turn_metrics:
        result = evaluate(
            test_cases=test_cases,
            metrics=single_turn_metrics,
            cache_config=cache,
            display_config=display,
        )
        passed = sum(case.success for case in result.test_results)
        print(f"Test-case results: {passed}/{len(result.test_results)} passed.")
    print(
        f"Evaluation finished for {len(test_cases)} scenarios "
        f"on {DEMO_DATE}: {len(trace_metrics)} trace and "
        f"{len(single_turn_metrics)} test-case metrics. See reports for scores."
    )


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Opt-in live refund-agent evaluation (API costs apply)"
    )
    parser.add_argument("--metric", choices=("all", *METRIC_NAMES), default="all")
    args = parser.parse_args(argv)
    run(args.metric)


if __name__ == "__main__":
    main()
