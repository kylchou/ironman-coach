"""Thin wrapper around Open-Meteo (https://open-meteo.com) -- free, no API
key or signup required for non-commercial use. Two endpoints:
  - api.open-meteo.com/v1/forecast    current conditions + upcoming days
  - archive-api.open-meteo.com/v1/archive   historical daily weather

All units requested in US customary (F / mph / inches) since that's what's
useful for a US-based dashboard.
"""

from datetime import date

import httpx

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

DAILY_FIELDS = "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,weather_code"
CURRENT_FIELDS = "temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m"

COMMON_PARAMS = {
    "temperature_unit": "fahrenheit",
    "wind_speed_unit": "mph",
    "precipitation_unit": "inch",
    "timezone": "auto",
}

# Standard WMO weather interpretation codes, as used by Open-Meteo.
# https://open-meteo.com/en/docs (see "WMO Weather interpretation codes")
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def describe_weather_code(code: int | None) -> str:
    if code is None:
        return "Unknown"
    return WMO_CODES.get(code, f"Unknown ({code})")


def fetch_forecast(lat: float, lon: float, days: int = 7) -> dict:
    """Current conditions plus the next `days` days of daily forecast."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": CURRENT_FIELDS,
        "daily": DAILY_FIELDS,
        "forecast_days": days,
        **COMMON_PARAMS,
    }
    resp = httpx.get(FORECAST_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_historical(lat: float, lon: float, start: date, end: date) -> dict:
    """Daily weather for a past date range (inclusive). Open-Meteo's archive
    has a few days' lag from "today", so very recent dates may come back
    empty -- use fetch_forecast (with its built-in recent-past coverage) for
    the last week or so instead.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": DAILY_FIELDS,
        **COMMON_PARAMS,
    }
    resp = httpx.get(ARCHIVE_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()
