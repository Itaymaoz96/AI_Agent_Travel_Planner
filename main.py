"""
Interactive REPL for the travel assistant.
Run with: python main.py
"""

from openai import OpenAI

from assistant import OpenAILLMClient, run_assistant
from config import OPENAI_API_KEY, OPENWEATHER_API_KEY
from preferences import load_user_preferences, save_user_preferences
from tools import tool_registry

PREFERENCES_PROMPT = (
    "Tell me your traveling preferences (e.g. are you vegetarian? do you like nightlife?) "
    "so I can plan your trip better."
)


def main():
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY is not set in .env")
        return

    client = OpenAI(api_key=OPENAI_API_KEY)
    llm = OpenAILLMClient(client)

    print("Hi! I'm your travel assistant. I can help you with weather, places of interest etc. (type 'quit' or 'exit' to stop)\n")
    if not OPENWEATHER_API_KEY:
        print("Note: OPENWEATHER_API_KEY not set in .env — weather queries will fail.\n")

    user_preferences = load_user_preferences()
    if not user_preferences:
        print(f"Assistant: {PREFERENCES_PROMPT}")
        try:
            prefs_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            prefs_input = ""
        if prefs_input:
            save_user_preferences(prefs_input)
            user_preferences = prefs_input
        print()

    conversation_history: list = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            print("Please enter a valid input")
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        streamed_response = False
        streamed_plan = False
        for event in run_assistant(
            conversation_history, user_input, llm, tool_registry, user_preferences=user_preferences
        ):
            kind = event[0]
            if kind == "plan_delta":
                chunk = event[1]
                if chunk:
                    if not streamed_plan:
                        print("\n[Plan]", end=" ", flush=True)
                        streamed_plan = True
                    print(chunk, end="", flush=True)
            elif kind == "plan":
                if streamed_plan:
                    print()
            elif kind == "delta":
                delta_text = event[1]
                if delta_text:
                    if not streamed_response:
                        print("\nAssistant:", end=" ", flush=True)
                        streamed_response = True
                    print(delta_text, end="", flush=True)
            elif kind == "result":
                response_text, weather_used, places_used, conversation_history = (
                    event[1], event[2], event[3], event[4]
                )
                if streamed_response:
                    print()
                else:
                    print("\nAssistant:", response_text)
                if weather_used or places_used:
                    parts = []
                    if weather_used:
                        parts.append("Weather API")
                    if places_used:
                        parts.append("Places (OpenStreetMap)")
                    print(f"\n  [Used: {', '.join(parts)}]")
                else:
                    print("\n  [No external APIs were used]")
        print()


if __name__ == "__main__":
    main()
