"""
Agentic Finance Chatbot — appears in every tab.
Uses LangGraph ReAct agent with finance tools + web search for real-time answers.
"""
import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from tools import CHAT_TOOLS

# ── System Prompt ─────────────────────────────────────────────────────────────
_CHAT_SYSTEM = """You are **Finley the Finance Tutor** 🦊 — an enthusiastic AI assistant for a stock market learning platform called "TradeFox: AI Paper Money Trading Academy!".

Your mission: make stock market, investing, economics, and financial concepts FUN, clear, and exciting for everyone.

**You have access to POWERFUL TOOLS — USE THEM:**
- `get_stock_fundamentals`: get P/E, P/B, ROE, market cap, and company info
- `get_stock_financials`: get Income Statement, Balance Sheet, Cash Flow
- `get_stock_news`: get the latest news headlines for a stock
- `get_analyst_recommendations`: get Wall Street analyst consensus
- `get_earnings_transcripts`: get earnings call context and guidance
- `get_macro_economic_data`: get current interest rates, Fed policy, and macro headlines
- `web_search_news`: search the internet for ANY current information: market news, economic trends, global events, etc.

**RULES:**
1. ALWAYS use tools when the user asks about a specific stock, market data, news, or current events. Do NOT make up data.
2. When asked about current events (elections, wars, tariffs, Fed decisions, crypto prices, etc.), use `web_search_news` to get the latest info.
3. Use simple, everyday language. Avoid jargon unless you immediately explain it.
4. Use emojis, analogies, and real-world comparisons to explain concepts.
5. Give concrete examples after explaining concepts.
6. Keep responses concise — 3 to 6 paragraphs max.
7. End responses with a follow-up suggestion or a "did you know?" fact to keep the learner engaged.
8. NEVER give actual financial advice or tell anyone what to buy/sell. You are educational only.
9. If the user asks about something outside of finance/economics, you may use web_search_news to find info, but gently redirect toward financial topics.
10. For kids/teens, use pizza 🍕, sports ⚽, games 🎮, and candy 🍬 analogies.
"""

# ── Suggested prompts per tab context ─────────────────────────────────────────
_SUGGESTIONS = {
    "education": [
        "What is a stock? Explain like I'm 10 🍎",
        "What's the difference between a bull and bear market?",
        "How does compound interest work?",
        "What is the S&P 500?",
        "What are dividends?",
        "How can a teenager start investing?",
    ],
    "screener": [
        "What does P/E ratio mean?",
        "How do I know if a stock is undervalued?",
        "What's the difference between market cap and revenue?",
        "What sectors are hot right now?",
        "Search for latest stock market news today",
        "What's happening with tech stocks this week?",
    ],
    "analyst": [
        "Analyze Apple (AAPL) fundamentals for me",
        "What's the latest news on Tesla?",
        "What do Wall Street analysts say about NVIDIA?",
        "Search for latest Federal Reserve interest rate news",
        "Explain what ROE means with an example",
        "What is a good P/E ratio?",
    ],
    "macro": [
        "What's the current state of the US economy?",
        "Search for latest inflation data",
        "How do tariffs affect the stock market?",
        "What happens to stocks when interest rates rise?",
        "Search for latest geopolitical news affecting markets",
        "What is quantitative easing?",
    ],
    "paper_trader": [
        "What is paper trading and why should I do it?",
        "What's the difference between a market order and limit order?",
        "How do I manage risk on a trade?",
        "What does position sizing mean?",
        "What is a stop-loss order?",
        "How do I calculate my portfolio return?",
    ],
}


def _get_or_create_agent(groq_api_key: str):
    """Get or create the cached LangGraph ReAct agent for the chatbot."""
    if "chat_agent" not in st.session_state:
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=groq_api_key,
            temperature=0.5,
        )
        st.session_state["chat_agent"] = create_react_agent(
            llm,
            tools=CHAT_TOOLS,
            prompt=_CHAT_SYSTEM,
        )
    return st.session_state["chat_agent"]


def render_chat(groq_api_key: str, tab_context: str = "education"):
    """
    Render the agentic chatbot UI. Call this inside any tab.

    Args:
        groq_api_key: Groq API key from st.secrets.
        tab_context: one of 'education', 'screener', 'analyst', 'macro', 'paper_trader'
    """
    st.markdown("---")
    st.subheader("🤖 Finley — Your AI Finance Tutor")
    st.caption("Powered by Llama 3.3 + real-time web search + financial data tools ⚡")

    if not groq_api_key:
        st.info(
            "💡 To activate the AI Tutor, add `GROQ_API_KEY` to `.streamlit/secrets.toml`. "
            "Get a **free key** at [console.groq.com](https://console.groq.com)."
        )
        return

    # Storage keys unique per tab so chat histories are separate
    display_key = f"chat_display_{tab_context}"    # list of {role, content} for rendering
    lc_key = f"chat_lc_{tab_context}"              # list of LangChain message objects for the agent
    pending_key = f"chat_pending_{tab_context}"

    if display_key not in st.session_state:
        st.session_state[display_key] = [
            {
                "role": "assistant",
                "content": (
                    "👋 Hi! I'm **Finley** 🦊, your AI Finance Tutor!\n\n"
                    "I can look up **real-time stock data**, **search the web** for the latest news, "
                    "and explain any finance concept in simple terms. Try one of the suggestions below, "
                    "or ask me anything! 💬"
                ),
            }
        ]
    if lc_key not in st.session_state:
        st.session_state[lc_key] = []

    # Render chat history
    for msg in st.session_state[display_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── Suggested question chips ──────────────────────────────────────────────
    suggestions = _SUGGESTIONS.get(tab_context, _SUGGESTIONS["education"])
    st.markdown("**💬 Quick questions — click to ask:**")
    cols = st.columns(3)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 3]:
            if st.button(suggestion, key=f"csug_{tab_context}_{i}", use_container_width=True):
                st.session_state[pending_key] = suggestion

    # ── Chat input ────────────────────────────────────────────────────────────
    typed_q = st.chat_input("Ask Finley anything…", key=f"cinput_{tab_context}")
    question = typed_q or st.session_state.pop(pending_key, None)

    if question:
        # Save user message to display history
        st.session_state[display_key].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # Run the agentic LangGraph agent
        with st.chat_message("assistant"):
            with st.spinner("🦊 Finley is researching…"):
                try:
                    agent = _get_or_create_agent(groq_api_key)

                    # Build input: use stored LangChain history (last 10 messages)
                    # plus current question
                    recent_lc = st.session_state[lc_key][-10:]
                    recent_lc_copy = list(recent_lc)  # shallow copy
                    recent_lc_copy.append(HumanMessage(content=question))
                    inputs = {"messages": recent_lc_copy}

                    # Stream through agent
                    final_answer = ""
                    tool_log = []
                    all_new_messages = []  # collect all messages from this run

                    for event in agent.stream(inputs, stream_mode="values"):
                        msg = event["messages"][-1]
                        all_new_messages = event["messages"]  # keep updating to get final state
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tc in msg.tool_calls:
                                tool_log.append(tc['name'])
                        if msg.type == "ai" and msg.content and (
                            not hasattr(msg, 'tool_calls') or not msg.tool_calls
                        ):
                            final_answer = msg.content

                    if not final_answer:
                        final_answer = "I wasn't able to generate a response. Please try rephrasing your question! 🤔"

                    # Store the FULL message sequence from this turn (user + tool calls + tool results + final AI)
                    # This preserves the tool execution context for future turns
                    # We only keep messages that were newly generated (after the recent_lc prefix)
                    prefix_len = len(recent_lc_copy) - 1  # -1 for the HumanMessage we added
                    new_msgs = all_new_messages[len(recent_lc):]  # everything after our prefix
                    st.session_state[lc_key].extend(new_msgs)

                    # Trim LangChain history to prevent unbounded growth (keep last 20 messages)
                    if len(st.session_state[lc_key]) > 20:
                        st.session_state[lc_key] = st.session_state[lc_key][-20:]

                    # Show tool usage if any
                    if tool_log:
                        tools_str = ", ".join(f"`{t}`" for t in tool_log)
                        st.caption(f"🛠️ Tools used: {tools_str}")

                    st.markdown(final_answer)

                except Exception as e:
                    final_answer = (
                        f"⚠️ Oops! Something went wrong: `{str(e)[:200]}`\n\n"
                        "Please try again — sometimes the AI service has momentary hiccups!"
                    )
                    st.markdown(final_answer)

        st.session_state[display_key].append({"role": "assistant", "content": final_answer})
        st.rerun()

