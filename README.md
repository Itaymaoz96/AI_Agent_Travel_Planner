# ✈️ Travel Assistant AI Agent

A conversational AI travel assistant that helps with **weather**, **places of interest**, and **trip planning**. It uses OpenAI for reasoning and calls external APIs for real-time weather (OpenWeatherMap) and places (OpenStreetMap / Overpass).

## Features

- **Weather** — Current temperature and 5-day forecasts for any city
- **Places** — Restaurants, museums, and parks via OpenStreetMap (Overpass API)
- **Trip planning** — Combines weather + places with LLM-generated suggestions (sights, activities, itineraries)
- **Two interfaces** — Terminal REPL or Streamlit web UI

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

- **OpenAI**: [API keys](https://platform.openai.com/api-keys) (required)
- **OpenWeatherMap**: [Sign up](https://openweathermap.org/api) for a free API key (required for weather; places work without it)

### 3. Run

**Terminal (REPL):**

```bash
python main.py
```

**Web UI (Streamlit):**

```bash
streamlit run streamlit_app.py
```

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

## Requirements

- Python 3.10+
- `openai` — LLM (OpenAI API)
- `python-dotenv` — load `.env`
- `streamlit` — optional, for the web UI

