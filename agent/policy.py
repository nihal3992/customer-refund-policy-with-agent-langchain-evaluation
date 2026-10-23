from datetime import date
from typing import Literal

from pydantic import BaseModel

from agent.data import users_data

DEMO_DATE = date(2026, 10, 22)


class RefundLine(BaseModel):
    name: str
    amount: int
    reason: Literal["eligible", "not purchased", "future purchase", "outside 30-day window"]


class RefundQuote(BaseModel):
    status: Literal["success", "user not found"]
    amount: int
    items: list[RefundLine]
    as_of: str


def quote_refund(user_id: str, items: list[str], *, as_of: date) -> RefundQuote:
    if not items or any(not item.strip() for item in items):
        raise ValueError("Request at least one non-empty item name.")
    if user_id not in users_data:
        return RefundQuote(status="user not found", amount=0, items=[], as_of=as_of.isoformat())
    orders = users_data[user_id]
    lines = []
    for name in dict.fromkeys(items):
        if name not in orders:
            lines.append(RefundLine(name=name, amount=0, reason="not purchased"))
            continue
        order = orders[name]
        age = (as_of - date.fromisoformat(order["date"])).days
        if age < 0:
            reason = "future purchase"
        elif age > 30:
            reason = "outside 30-day window"
        else:
            reason = "eligible"
        lines.append(
            RefundLine(
                name=name,
                amount=order["price"] if reason == "eligible" else 0,
                reason=reason,
            )
        )
    return RefundQuote(
        status="success",
        amount=sum(line.amount for line in lines),
        items=lines,
        as_of=as_of.isoformat(),
    )
