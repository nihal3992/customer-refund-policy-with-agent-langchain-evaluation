from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from deepeval.models import DeepEvalBaseLLM
from langchain_core.messages import AIMessage

from agent.objects import Answer
from evaluation import eval_all
from evaluation.dataset import dataset


class OfflineJudge(DeepEvalBaseLLM):
    def load_model(self):
        return self

    def generate(self, prompt, **kwargs):
        raise AssertionError("Offline tests must not call a judge")

    async def a_generate(self, prompt, **kwargs):
        raise AssertionError("Offline tests must not call a judge")

    def get_model_name(self):
        return "offline-judge"


def test_all_metrics_construct_with_installed_deepeval(monkeypatch):
    monkeypatch.setattr(eval_all, "evaluator_model", lambda: OfflineJudge())
    traces, singles = eval_all.build_metrics()
    assert len(traces) == 4
    assert len(singles) == 3
    assert all(metric.threshold == 0.8 for metric in [*traces, *singles])
    assert singles[1].should_consider_ordering is True


def test_dataset_and_tool_order():
    assert len(dataset.goldens) == 7
    for golden in dataset.goldens:
        assert isinstance(golden.input, str)
        assert isinstance(golden.expected_output, str)
        names = [tool.name for tool in golden.expected_tools]
        if "issue_refund_ticket" in names:
            assert names == [
                "get_user_order_history",
                "get_today_date",
                "calculate_right_refund_amount",
                "issue_refund_ticket",
            ]


def response():
    return {
        "structured_response": Answer(answer="Simulated refund: $23.", conversation=False),
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "get_user_order_history", "args": {"user_id": "user123"}, "id": "one"},
                    {"name": "Answer", "args": {"answer": "Simulated refund: $23."}, "id": "two"},
                ],
            )
        ],
    }


def test_test_case_contains_answer_and_business_tool_arguments():
    case = eval_all.make_test_case(dataset.goldens[1], response())
    assert case.actual_output == "Simulated refund: $23."
    assert len(case.tools_called) == 1
    assert case.tools_called[0].input_parameters == {"user_id": "user123"}


@pytest.mark.parametrize("trace_enabled", [False, True])
def test_runner_wires_callbacks_and_unique_threads(monkeypatch, trace_enabled):
    trace_metrics = [Mock()] if trace_enabled else []
    singles = [Mock()]
    monkeypatch.setattr(eval_all, "build_metrics", lambda selected: (trace_metrics, singles))
    fake_agent = Mock()
    fake_agent.invoke.return_value = response()
    monkeypatch.setattr(eval_all, "build_agent", lambda **kwargs: fake_agent)
    iterator = Mock(return_value=iter(dataset.goldens))
    monkeypatch.setattr(
        eval_all, "dataset", SimpleNamespace(goldens=dataset.goldens, evals_iterator=iterator)
    )
    evaluate = Mock(return_value=SimpleNamespace(test_results=[]))
    monkeypatch.setattr(eval_all, "evaluate", evaluate)
    eval_all.run()
    calls = fake_agent.invoke.call_args_list
    assert len(calls) == 7
    threads = {call.kwargs["config"]["configurable"]["thread_id"] for call in calls}
    assert len(threads) == 7
    assert all(bool(call.kwargs["config"]["callbacks"]) == trace_enabled for call in calls)
    assert len(evaluate.call_args.kwargs["test_cases"]) == 7
    assert evaluate.call_args.kwargs["metrics"] is singles
    assert iterator.called == trace_enabled
