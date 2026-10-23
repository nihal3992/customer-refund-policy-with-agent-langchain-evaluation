from datetime import timedelta

import pytest

from agent.data import users_data
from agent.policy import DEMO_DATE, quote_refund
from agent.tools import build_tools


@pytest.mark.parametrize(
    ("user", "items", "amount"),
    [
        ("user123", ["book", "pen"], 30),
        ("user123", ["book"], 23),
        ("user126", ["water_bottle"], 0),
        ("user126", ["backpack", "water_bottle"], 45),
        ("user123", ["sneakers"], 0),
        ("user999", ["book"], 0),
        ("user123", ["book", "book"], 23),
    ],
)
def test_reference_quotes(user, items, amount):
    quote = quote_refund(user, items, as_of=DEMO_DATE)
    assert quote.amount == amount
    assert quote.status == ("user not found" if user == "user999" else "success")


@pytest.mark.parametrize(
    ("age", "amount", "reason"),
    [
        (-1, 0, "future purchase"),
        (0, 10, "eligible"),
        (30, 10, "eligible"),
        (31, 0, "outside 30-day window"),
    ],
)
def test_policy_boundaries(monkeypatch, age, amount, reason):
    monkeypatch.setitem(
        users_data,
        "boundary",
        {"item": {"price": 10, "date": (DEMO_DATE - timedelta(days=age)).isoformat()}},
    )
    quote = quote_refund("boundary", ["item"], as_of=DEMO_DATE)
    assert quote.amount == amount
    assert quote.items[0].reason == reason


@pytest.mark.parametrize("items", [[], [""], [" "]])
def test_empty_items_are_explicit_errors(items):
    with pytest.raises(ValueError, match="at least one"):
        quote_refund("user123", items, as_of=DEMO_DATE)


def test_future_purchase_is_rejected():
    quote = quote_refund("user129", ["folder"], as_of=DEMO_DATE)
    assert quote.amount == 0
    assert quote.items[0].reason == "future purchase"


def test_ticket_revalidates_amount_and_customer():
    tools = {tool.name: tool for tool in build_tools(as_of=DEMO_DATE)}
    args = {"user_id": "user123", "item_name": [{"name": "book"}]}
    assert tools["calculate_right_refund_amount"].invoke(args)["amount"] == 23
    ticket = tools["issue_refund_ticket"]
    assert ticket.invoke({**args, "refund_amount": 30})["status"] == "invalid refund amount"
    assert ticket.invoke({**args, "refund_amount": 0})["status"] == "invalid refund amount"
    assert ticket.invoke({**args, "refund_amount": 23}) == {
        "status": "success",
        "amount": 23,
        "simulated": True,
    }
    assert ticket.invoke({**args, "user_id": "user999", "refund_amount": 23})["status"] == (
        "user not found"
    )
    assert tools["get_today_date"].invoke({})["date"] == DEMO_DATE.isoformat()


def test_ticket_cannot_refund_an_unowned_or_expired_item():
    ticket = next(
        tool for tool in build_tools(as_of=DEMO_DATE) if tool.name == "issue_refund_ticket"
    )
    for user, item in [("user123", "sneakers"), ("user126", "water_bottle"), ("user129", "folder")]:
        result = ticket.invoke(
            {"user_id": user, "item_name": [{"name": item}], "refund_amount": 10}
        )
        assert result["status"] == "invalid refund amount"
