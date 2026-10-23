from deepeval.dataset import EvaluationDataset, Golden
from deepeval.test_case import ToolCall

dataset = EvaluationDataset(
    goldens=[
        Golden(
            input="I am user123, I want to request a refund for a book and the pen",
            expected_output="A simulated refund ticket for $30 has been issued for the book and pen.",
            expected_tools=[
                ToolCall(name="get_user_order_history"),
                ToolCall(name="get_today_date"),
                ToolCall(name="calculate_right_refund_amount"),
                ToolCall(name="issue_refund_ticket"),
            ],
        ),
        Golden(
            input="I am user123, I want to request a refund for a book",
            expected_output="A simulated refund ticket for $23 has been issued for the book only.",
            expected_tools=[
                ToolCall(name="get_user_order_history"),
                ToolCall(name="get_today_date"),
                ToolCall(name="calculate_right_refund_amount"),
                ToolCall(name="issue_refund_ticket"),
            ],
        ),
        Golden(
            input=(
                "I am user123, I want no refund for a book and the pen. "
                "I want to know what I purchased"
            ),
            expected_output="You purchased a book for $23 and a pen for $7. No refund was issued.",
            expected_tools=[ToolCall(name="get_user_order_history")],
        ),
        Golden(
            input="I am user999, I want a refund for a book",
            expected_output="Username is not valid, please provide a valid username.",
            expected_tools=[ToolCall(name="get_user_order_history")],
        ),
        Golden(
            input="I am user126, I want to request a refund for a water_bottle",
            expected_output="No refund was issued: the water bottle is outside the 30-day window.",
            expected_tools=[
                ToolCall(name="get_user_order_history"),
                ToolCall(name="get_today_date"),
                ToolCall(name="calculate_right_refund_amount"),
            ],
        ),
        Golden(
            input="I am user126, I want to request a refund for a backpack and a water_bottle",
            expected_output=(
                "A simulated refund ticket for $45 has been issued for the backpack only. "
                "The water bottle is outside the 30-day window."
            ),
            expected_tools=[
                ToolCall(name="get_user_order_history"),
                ToolCall(name="get_today_date"),
                ToolCall(name="calculate_right_refund_amount"),
                ToolCall(name="issue_refund_ticket"),
            ],
        ),
        Golden(
            input="I am user123, I want to request a refund for a sneakers",
            expected_output="No refund was issued because you did not purchase sneakers.",
            expected_tools=[
                ToolCall(name="get_user_order_history"),
                ToolCall(name="get_today_date"),
                ToolCall(name="calculate_right_refund_amount"),
            ],
        ),
    ]
)
