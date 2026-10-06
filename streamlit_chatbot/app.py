import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from groq import Groq


load_dotenv(Path(__file__).resolve().parent / ".env")

# Configure the page before rendering any Streamlit elements.
st.set_page_config(
    page_title="BiteLine | Food Assistant",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODEL = "openai/gpt-oss-120b"
WELCOME_MESSAGE = (
    "Hi, I'm **BiteLine**. Tell me what you're craving, your dietary preferences, "
    "or which meal you're planning, and I'll help you find a delicious direction. "
    "I can suggest ideas, but I can't place orders or take payments."
)
SYSTEM_PROMPT = """You are BiteLine, a friendly food-ordering assistant.
Help users with food and restaurant-style recommendations, menu ideas, vegetarian
and non-vegetarian choices, meal planning, and food preferences. Ask a brief
follow-up question when it would improve your recommendation.

You are not connected to a live restaurant, menu, delivery, or payment service.
Treat restaurant names, dishes, prices, opening hours, and availability as sample
or general information, and say so clearly. Never imply that a real order,
reservation, or payment has been placed or completed. You can help the user make
an order plan, but be clear that they must place it with a real provider."""

# A little custom styling gives the chat a warm, food-focused identity.
st.markdown(
    """
    <style>
    :root {
        --bite-ink: #17251e;
        --bite-muted: #68766e;
        --bite-orange: #f46a35;
        --bite-orange-dark: #d84d20;
        --bite-cream: #fffaf4;
        --bite-line: #eee5db;
        --bite-green: #1c382b;
    }
    .stApp {
        background:
            radial-gradient(ellipse at 95% 0%, rgba(255, 218, 190, .36), transparent 31rem),
            var(--bite-cream);
        color: var(--bite-ink);
    }
    [data-testid="stSidebar"] {
        background: var(--bite-green);
    }
    [data-testid="stSidebar"] * {
        color: #f8f4eb;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #c9d5cb;
    }
    .brand-mark {
        font-size: 14px;
        font-weight: 800;
        letter-spacing: 1.4px;
        color: #ff9a69;
        text-transform: uppercase;
    }
    .side-copy {
        color: #c9d5cb;
        font-size: 13px;
        line-height: 1.5;
        margin: 4px 0 18px;
    }
    .hero-kicker {
        color: var(--bite-orange-dark);
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 7px;
    }
    .hero-title {
        color: var(--bite-ink);
        font-family: Georgia, 'Times New Roman', serif;
        font-size: clamp(32px, 4vw, 48px);
        font-weight: 700;
        line-height: 1.08;
        margin: 0;
    }
    .hero-subtitle {
        color: var(--bite-muted);
        font-size: 15px;
        line-height: 1.6;
        margin: 12px 0 0;
        max-width: 680px;
    }
    .model-note {
        color: var(--bite-muted);
        font-size: 12px;
        padding-top: 12px;
        text-align: right;
    }
    [data-testid="stChatMessage"] {
        border: 1px solid var(--bite-line);
        border-radius: 8px;
        background: rgba(255, 255, 255, .78);
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] * {
        color: var(--bite-ink) !important;
    }
    [data-testid="stChatInput"] {
        border-color: #dfd2c5;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button {
        border: 1px solid rgba(255, 255, 255, .2);
        border-radius: 7px;
        background: rgba(255, 255, 255, .08);
        color: white;
        min-height: 42px;
        text-align: left;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button:hover {
        border-color: #ff9a69;
        background: rgba(255, 154, 105, .16);
        color: white;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"]:has(*) {
        font-weight: 600;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
        background: var(--bite-orange);
        border-color: var(--bite-orange);
        color: white;
    }
    @media (max-width: 640px) {
        .model-note { text-align: left; padding-top: 0; }
        .hero-title { font-size: 34px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Keep the conversation in Streamlit's per-user session state.
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": WELCOME_MESSAGE}
    ]
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


# The sidebar provides quick food prompts and a way to start over.
with st.sidebar:
    st.markdown('<div class="brand-mark">🍊 BiteLine</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="side-copy">A little inspiration for your next meal.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("#### Explore a craving")

    food_categories = [
        ("🍕 Pizza", "I'm craving pizza. Suggest a few styles and toppings."),
        ("🍔 Burger", "Help me choose a burger, including a vegetarian option."),
        ("🍛 Biryani", "Suggest biryani styles and sides for lunch or dinner."),
        ("🥘 Indian Food", "Recommend a balanced Indian meal with a few dishes."),
        ("🥗 Healthy Food", "Suggest a satisfying, healthy meal based on common preferences."),
    ]
    for label, prompt_text in food_categories:
        if st.button(label, key=f"category_{label}", use_container_width=True):
            st.session_state.pending_prompt = prompt_text

    st.divider()
    if st.button("🧹  Clear chat", key="clear_chat", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": WELCOME_MESSAGE}
        ]
        st.session_state.pending_prompt = None
        st.rerun()

# The main header keeps the purpose and model visible without crowding the chat.
header, model_info = st.columns([5, 2], vertical_alignment="center")
with header:
    st.markdown(
        '<div class="hero-kicker">Your next meal starts here</div>'
        '<h1 class="hero-title">What sounds good today?</h1>'
        '<p class="hero-subtitle">Get thoughtful food ideas for your taste, mood, '
        'and meal time.</p>',
        unsafe_allow_html=True,
    )
with model_info:
    st.markdown(
        f'<div class="model-note">Powered by Groq · {MODEL}</div>',
        unsafe_allow_html=True,
    )

st.caption(
    "Restaurant, menu, price, and availability details are general examples, "
    "not live listings. This assistant cannot place orders or process payments."
)
st.divider()

# Render the saved conversation before handling the newest message.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# A category button and the text box both feed the same chat flow.
typed_prompt = st.chat_input("Ask for a meal idea, dish, or recommendation…")
category_prompt = st.session_state.pending_prompt
st.session_state.pending_prompt = None
prompt = typed_prompt or category_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    assistant_reply = ""
    with st.chat_message("assistant"):
        with st.spinner("Thinking up something delicious…"):
            api_key = os.getenv("GROQ_API_KEY", "").strip()
            if not api_key:
                api_key = str(st.secrets.get("GROQ_API_KEY", "")).strip()
            if not api_key or api_key.lower() == "your_groq_api_key_here":
                assistant_reply = (
                    "Add your Groq key as `GROQ_API_KEY=...` in "
                    "`streamlit_chatbot/.env` or in `.streamlit/secrets.toml`."
                )
            else:
                try:
                    client = Groq(api_key=api_key)
                    
                    completion = client.chat.completions.create(
                        model=MODEL,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            *st.session_state.messages,
                        ],
                    )
                    assistant_reply = completion.choices[0].message.content or (
                        "I couldn't come up with a response just now. Try asking again."
                    )
                except Exception as error:
                    assistant_reply = (
                        "I couldn't reach Groq just now. Check your API key and "
                        "connection, then try again."
                    )
                    st.error(f"Groq request failed: {error}")
        st.markdown(assistant_reply)

    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_reply}
    )
