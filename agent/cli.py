import argparse
from datetime import date
from uuid import uuid4

from agent.agent import build_agent
from agent.policy import DEMO_DATE, quote_refund


def main() -> None:
    parser = argparse.ArgumentParser(description="Refund assistant sandbox")
    parser.add_argument(
        "--demo", action="store_true", help="Run the policy without an LLM or API key"
    )
    parser.add_argument("--user", default="user126", help="Synthetic customer for --demo")
    parser.add_argument("--items", nargs="+", default=["backpack", "water_bottle"])
    parser.add_argument(
        "--date", type=date.fromisoformat, help="Override the policy reference date"
    )
    args = parser.parse_args()
    if args.demo:
        print("OFFLINE POLICY DEMO - no LLM, no ticket, no payment")
        print(
            quote_refund(args.user, args.items, as_of=args.date or DEMO_DATE).model_dump_json(
                indent=2
            )
        )
        return
    agent = build_agent(as_of=args.date)
    config = {"configurable": {"thread_id": str(uuid4())}}
    print("Refund assistant sandbox. Tickets are simulated. Type /exit to leave.")
    while True:
        try:
            text = input("You: ").strip()
        except EOFError, KeyboardInterrupt:
            print("\nConversation ended.")
            return
        if text == "/exit":
            return
        if not text:
            continue
        response = agent.invoke({"messages": [{"role": "user", "content": text}]}, config=config)
        answer = response["structured_response"]
        print(f"Assistant: {answer.answer}")
        if not answer.conversation:
            print("Task complete. You can ask another question or type /exit.")


if __name__ == "__main__":
    main()
