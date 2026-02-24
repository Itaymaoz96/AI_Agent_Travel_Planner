"""
Travel assistant UI with Streamlit.
Run with: streamlit run streamlit_app.py
"""

import streamlit as st
from openai import OpenAI

from assistant import OpenAILLMClient, run_assistant
from config import OPENAI_API_KEY, OPENWEATHER_API_KEY
from preferences import load_user_preferences, save_user_preferences
from tools import tool_registry

PREFERENCES_PROMPT = (
    "Tell me your traveling preferences (e.g. are you vegetarian? do you like nightlife?) "
    "so I can plan your trip better."
)

st.set_page_config(page_title="Travel Assistant", page_icon="✈️", layout="centered")

if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY is not set in .env")
    st.stop()

user_preferences = load_user_preferences()
if not user_preferences:
    st.title("Travel Assistant")
    st.markdown(f"**{PREFERENCES_PROMPT}**")
    with st.form("preferences_form"):
        prefs_input = st.text_area(
            "Your preferences",
            placeholder="e.g. I'm vegetarian, I love nightlife and live music, prefer walking over tours",
            label_visibility="collapsed",
        )
        if st.form_submit_button("Save and start"):
            if prefs_input and prefs_input.strip():
                save_user_preferences(prefs_input.strip())
                st.rerun()
            else:
                st.warning("Please enter at least something so I can personalize your trip.")
    st.stop()

if "display_messages" not in st.session_state:
    st.session_state.display_messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

client = OpenAI(api_key=OPENAI_API_KEY)
llm = OpenAILLMClient(client)

if not OPENWEATHER_API_KEY:
    st.warning("OPENWEATHER_API_KEY not set in .env — weather queries will fail.")

st.title("Travel Assistant")
st.caption("Weather, places & trip ideas")

for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if msg.get("plan"):
                with st.expander("Plan"):
                    st.markdown(msg["plan"])
            if msg.get("weather_used") or msg.get("places_used"):
                badges = []
                if msg.get("weather_used"):
                    badges.append("Weather API")
                if msg.get("places_used"):
                    badges.append("Places (OpenStreetMap)")
                st.caption("Used: " + ", ".join(badges))

prompt = st.chat_input("Ask about weather, places, or plan a trip…")
if prompt:
    st.session_state.display_messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        plan_expander = st.expander("Plan", expanded=True)
        plan_placeholder = plan_expander.empty()
        stream_placeholder = st.empty()
        badges_placeholder = st.empty()

        plan_parts = []
        response_parts = []
        response_text = ""
        weather_used = False
        places_used = False
        new_history = st.session_state.conversation_history

        for event in run_assistant(
            st.session_state.conversation_history,
            prompt,
            llm,
            tool_registry,
            user_preferences=user_preferences,
        ):
            kind = event[0]
            if kind == "plan_delta":
                chunk = event[1]
                if chunk:
                    plan_parts.append(chunk)
                    plan_placeholder.markdown("".join(plan_parts))
            elif kind == "plan":
                plan_text = event[1] or ""
                plan_placeholder.markdown(plan_text)
            elif kind == "delta":
                response_parts.append(event[1])
                stream_placeholder.markdown("".join(response_parts))
            elif kind == "result":
                response_text, weather_used, places_used, new_history = (
                    event[1],
                    event[2],
                    event[3],
                    event[4],
                )
                stream_placeholder.markdown(response_text)
                if weather_used or places_used:
                    parts = []
                    if weather_used:
                        parts.append("Weather API")
                    if places_used:
                        parts.append("Places (OpenStreetMap)")
                    badges_placeholder.caption("Used: " + ", ".join(parts))

        st.session_state.conversation_history = new_history
        st.session_state.display_messages.append(
            {
                "role": "assistant",
                "content": response_text or "".join(response_parts),
                "plan": "".join(plan_parts),
                "weather_used": weather_used,
                "places_used": places_used,
            }
        )

    st.rerun()
