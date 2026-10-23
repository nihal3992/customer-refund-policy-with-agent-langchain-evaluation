import logging
from datetime import date

from langchain.tools import tool
from langchain_core.tools import BaseTool

from agent.data import users_data
from agent.objects import PurchaseItem
from agent.policy import quote_refund

logger = logging.getLogger(__name__)
TOOL_NAMES = (
    "get_user_order_history",
    "calculate_right_refund_amount",
    "issue_refund_ticket",
    "get_today_date",
)


def build_tools(*, as_of: date | None = None) -> list[BaseTool]:
    def today() -> date:
        return as_of if as_of is not None else date.today()

    @tool
    def get_user_order_history(user_id: str) -> dict:
        """Look up a customer's purchases by exact username."""
        if user_id not in users_data:
            logger.warning("Unknown customer: %s", user_id)
            return {"status": "user not found"}
        return users_data[user_id]

    @tool
    def calculate_right_refund_amount(user_id: str, item_name: list[PurchaseItem]) -> dict:
        """Calculate a refund for requested items, with eligibility and exclusion reasons."""
        result = quote_refund(user_id, [item.name for item in item_name], as_of=today())
        if result.status != "success":
            logger.warning("Cannot calculate refund for unknown customer: %s", user_id)
        return result.model_dump()

    @tool
    def issue_refund_ticket(
        user_id: str, refund_amount: int, item_name: list[PurchaseItem]
    ) -> dict:
        """Simulate a ticket only if the amount matches eligible requested purchases."""
        quote = quote_refund(user_id, [item.name for item in item_name], as_of=today())
        if quote.status != "success":
            logger.warning("Ticket rejected for unknown customer: %s", user_id)
            return {"status": "user not found", "simulated": True}
        if refund_amount <= 0 or refund_amount != quote.amount:
            logger.warning("Ticket rejected: requested amount does not match eligible purchases")
            return {
                "status": "invalid refund amount",
                "expected_amount": quote.amount,
                "simulated": True,
            }
        return {"status": "success", "amount": quote.amount, "simulated": True}

    @tool
    def get_today_date() -> dict:
        """Return the reference date used by the refund policy."""
        return {"status": "success", "date": today().isoformat()}

    return [
        get_user_order_history,
        calculate_right_refund_amount,
        issue_refund_ticket,
        get_today_date,
    ]
