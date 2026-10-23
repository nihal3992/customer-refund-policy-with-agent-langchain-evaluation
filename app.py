import logging
from uuid import uuid4

import streamlit as st
from langgraph.errors import GraphRecursionError
from openai import OpenAIError

from agent.agent import build_agent
from agent.data import users_data
from agent.policy import DEMO_DATE, quote_refund
from agent.tools import TOOL_NAMES

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Refund Lab | AIAgente", page_icon=":receipt:", layout="wide")
st.markdown(
    """
    <style>
    .stApp {background: #0b1220; color: #edf2fa;}
    [data-testid="stSidebar"] {background: #111d31;}
    .block-container {max-width: 1150px; padding-top: 2.5rem;}
    h1, h2, h3 {letter-spacing: -0.03em;}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("Refund Lab")
    st.caption("AIAgente / customer support sandbox")
    mode = st.radio("Workspace", ["Policy explorer", "Live agent chat"])
    st.divider()
    st.markdown("**Built with**\n\nLangChain · LangGraph · DeepEval · Streamlit")
    st.info("Synthetic customers only. Tickets are simulated. No money moves.")
    st.caption(
        "Policy explorer works offline. Live chat sends requests to your configured provider."
    )

st.caption("TOOL-DRIVEN SUPPORT / EVALUATION-FIRST ENGINEERING")
st.title("A refund decision you can inspect.")
st.write(
    "Explore the policy without an API key, or talk to an LLM-powered assistant "
    "and inspect the tools behind its answer."
)
columns = st.columns(3)
columns[0].metric("Refund window", "30 days", "Inclusive of day 30", delta_color="off")
columns[1].metric("Reference scenarios", "7")
columns[2].metric("Evaluation metrics", "7", "Opt-in live evaluation", delta_color="off")
st.divider()

if mode == "Policy explorer":
    st.subheader("Try the rules, not a scripted chatbot")
    st.write(
        "This deterministic workspace runs the same policy used by the agent's tools. "
        "It does not call an LLM or issue a ticket."
    )
    with st.form("policy"):
        left, right = st.columns(2)
        user_id = left.selectbox("Synthetic customer", list(users_data), index=3)
        as_of = right.date_input("Reference date", value=DEMO_DATE)
        item_text = st.text_input(
            "Requested items (comma-separated)", value="backpack, water_bottle"
        )
        submitted = st.form_submit_button("Check refund eligibility", type="primary")
    if submitted:
        items = [item.strip() for item in item_text.split(",")]
        if any(not item for item in items):
            st.error("Enter one or more item names, separated by commas, without empty entries.")
        else:
            quote = quote_refund(user_id, items, as_of=as_of)
            st.metric("Eligible refund", f"${quote.amount}")
            st.dataframe(
                [line.model_dump() for line in quote.items],
                hide_index=True,
                use_container_width=True,
            )
            st.caption(f"Evaluated on {quote.as_of}. Duplicate item names count only once.")
    with st.expander("Browse synthetic purchases", expanded=True):
        st.dataframe(
            [
                {"user": user, "item": item, **order}
                for user, orders in users_data.items()
                for item, order in orders.items()
            ],
            hide_index=True,
            use_container_width=True,
        )
else:
    st.subheader("Live agent workspace")
    st.caption(
        "Uses the current system date unless you choose the fixed demo date. "
        "Configure AGENT_MODEL and provider credentials in .env first."
    )
    fixed_date = st.checkbox("Use demo date: 2026-10-22", value=True)
    if st.session_state.get("fixed_date") != fixed_date:
        st.session_state.pop("assistant", None)
        st.session_state["chat"] = []
        st.session_state["thread_id"] = str(uuid4())
        st.session_state["fixed_date"] = fixed_date
    if st.button("New conversation"):
        st.session_state.pop("assistant", None)
        st.session_state["chat"] = []
        st.session_state["thread_id"] = str(uuid4())
    st.session_state.setdefault("chat", [])
    st.session_state.setdefault("thread_id", str(uuid4()))
    st.info("Try: I am user126. Please refund my backpack and water_bottle.")
    for entry in st.session_state["chat"]:
        with st.chat_message(entry["role"]):
            st.write(entry["content"])
            if entry.get("tools"):
                with st.expander("Tool calls"):
                    st.json(entry["tools"])
    if prompt := st.chat_input("Ask about a purchase or request a refund"):
        st.session_state["chat"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        try:
            if "assistant" not in st.session_state:
                st.session_state["assistant"] = build_agent(as_of=DEMO_DATE if fixed_date else None)
            with st.spinner("Checking purchases and refund policy..."):
                response = st.session_state["assistant"].invoke(
                    {"messages": [{"role": "user", "content": prompt}]},
                    config={"configurable": {"thread_id": st.session_state["thread_id"]}},
                )
            messages = response["messages"]
            last_user = max(
                index for index, message in enumerate(messages) if message.type == "human"
            )
            tools = [
                {"name": call["name"], "arguments": call["args"]}
                for message in messages[last_user + 1 :]
                for call in getattr(message, "tool_calls", [])
                if call["name"] in TOOL_NAMES
            ]
            answer = response["structured_response"].answer
            st.session_state["chat"].append(
                {"role": "assistant", "content": answer, "tools": tools}
            )
            with st.chat_message("assistant"):
                st.write(answer)
                if tools:
                    with st.expander("Tool calls"):
                        st.json(tools)
        except (ValueError, OpenAIError, GraphRecursionError) as error:
            logger.exception("Live agent request failed")
            st.error(
                f"Live request failed ({type(error).__name__}). Check your model configuration, "
                "credentials, and terminal logs. Start a new conversation before retrying."
            )
