# ✈️ Travel Assistant AI Agent

A conversational AI travel assistant that helps with **trip planning**. It uses OpenAI and calls external APIs for real-time weather (OpenWeatherMap) and places (OpenStreetMap / Overpass).

## Features

- **Weather** — Current temperature and 5-day forecasts for any city
- **Places** — Restaurants, museums, and parks via OpenStreetMap (Overpass API)
- **Trip planning** — Combines weather + places with LLM-generated suggestions (sights, activities, itineraries)
- **User preferences** — On first run, the assistant asks for your travel preferences (e.g. diet, nightlife, activities); these are saved in a local `user_preferences.txt` and used to personalize recommendations in every session

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/Itaymaoz96/travel_assistant_ai_agent.git
cd travel_assistant_ai_agent
pip install -r requirements.txt
```

### 2. Configure API keys

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
```

### 3. Run


**Web UI (Streamlit):**

```bash
streamlit run streamlit_app.py
```

On first run (or if `user_preferences.txt` is missing or empty), the assistant will ask for your traveling preferences so it can plan trips better. Your reply is saved locally and reused in future sessions.

## Example prompts

- *"What's the weather in Paris this week?"*
- *"Temperature in Tokyo and London tomorrow"*
- *"Suggest restaurants and a museum in Berlin"*
- *"Plan a 2-day trip to Amsterdam with weather and things to do"*

## Project structure

| File | Description |
|------|-------------|
| `main.py` | CLI REPL — chat in the terminal |
| `streamlit_app.py` | Streamlit web UI |
| `assistant.py` | Core orchestration: plan → execute tools → stream response |
| `tools.py` | Tool implementations (weather, places) and registry |
| `prompts.py` | System prompt and plan/execute scaffolding |
| `config.py` | Loads `.env` and API URLs/constants |
| `preferences.py` | Load/save user travel preferences to a local `.txt` file |
| `user_preferences.txt` | Your saved preferences (created on first run; optional `USER_PREFERENCES_PATH` in `.env` to override path) |

## Requirements

- Python 3.10+
- `openai` — LLM (OpenAI API)
- `python-dotenv` — load `.env`
- `streamlit` — optional, for the web UI

