"""
Configuration and constants. Loads environment variables from .env.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# API keys (from .env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Weather API (current + 5-day forecast)
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# OpenStreetMap: no API key required (use a descriptive User-Agent per usage policy)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
REQUEST_HEADERS = {"User-Agent": "AssistantApp/1.0 (travel assistant; python)"}

# Overpass API: only these three categories (other POIs/attractions are LLM-generated)
PLACE_CATEGORIES = {
    "restaurant": '["amenity"~"restaurant|fast_food"]',
    "museum": '["tourism"~"museum|gallery"]',
    "park": '["leisure"~"park|garden"]',
}
