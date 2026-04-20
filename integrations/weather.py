"""
Weather integration for Alma, Michigan.
Uses Open-Meteo free API (no API key needed).

Alma, MI coordinates: 43.3789° N, 84.6597° W
"""

import requests
from datetime import date
import streamlit as st

# Alma, Michigan coordinates
ALMA_LAT = 43.3789
ALMA_LON = -84.6597
ALMA_TIMEZONE = "America/Detroit"

# WMO Weather codes mapping
WMO_CODES = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    56: "Light Freezing Drizzle",
    57: "Dense Freezing Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    66: "Light Freezing Rain",
    67: "Heavy Freezing Rain",
    71: "Slight Snow",
    73: "Moderate Snow",
    75: "Heavy Snow",
    77: "Snow Grains",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    85: "Slight Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm w/ Slight Hail",
    99: "Thunderstorm w/ Heavy Hail",
}

# Weather conditions that typically affect staffing
STAFFING_IMPACT_CODES = {
    56, 57,      # Freezing drizzle
    65, 66, 67,  # Heavy/freezing rain
    73, 75,      # Moderate/heavy snow
    77,          # Snow grains
    82,          # Violent rain showers
    85, 86,      # Snow showers
    95, 96, 99,  # Thunderstorms
}


def _wmo_to_condition(code):
    """Convert WMO weather code to human-readable condition."""
    return WMO_CODES.get(code, "Unknown ({})".format(code))


def _wmo_to_simple(code):
    """Convert WMO code to simple category for the dropdown."""
    if code in (0, 1):
        return "Clear"
    elif code in (2, 3):
        return "Cloudy"
    elif code in (45, 48):
        return "Fog"
    elif code in (51, 53, 55, 61, 63, 65, 80, 81, 82):
        return "Rain"
    elif code in (56, 57, 66, 67):
        return "Freezing Rain"
    elif code in (71, 73, 75, 77, 85, 86):
        return "Snow"
    elif code in (95, 96, 99):
        return "Storm"
    return "Other"


def _may_affect_staffing(code):
    """Check if weather code typically affects staffing."""
    return code in STAFFING_IMPACT_CODES


@st.cache_data(ttl=900)  # Cache 15 min
def fetch_current_weather():
    """
    Fetch current weather for Alma, MI.
    Returns dict with: condition, temperature_f, wind_mph, description,
                       weather_code, may_affect_staffing
    Returns None on error.
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": ALMA_LAT,
            "longitude": ALMA_LON,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_gusts_10m,precipitation",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": ALMA_TIMEZONE,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current", {})
        code = current.get("weather_code", 0)

        return {
            "condition": _wmo_to_simple(code),
            "description": _wmo_to_condition(code),
            "temperature_f": current.get("temperature_2m"),
            "feels_like_f": current.get("apparent_temperature"),
            "humidity_pct": current.get("relative_humidity_2m"),
            "wind_mph": current.get("wind_speed_10m"),
            "wind_gusts_mph": current.get("wind_gusts_10m"),
            "precipitation_in": current.get("precipitation"),
            "weather_code": code,
            "may_affect_staffing": _may_affect_staffing(code),
        }
    except Exception:
        return None


@st.cache_data(ttl=1800)  # Cache 30 min
def fetch_daily_forecast(target_date=None):
    """
    Fetch daily forecast for Alma, MI for a specific date.
    Returns dict with: condition, high_f, low_f, description,
                       precipitation_sum, wind_max_mph, may_affect_staffing
    Returns None on error.
    """
    if target_date is None:
        target_date = date.today()

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": ALMA_LAT,
            "longitude": ALMA_LON,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,wind_gusts_10m_max",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": ALMA_TIMEZONE,
            "start_date": target_date.isoformat(),
            "end_date": target_date.isoformat(),
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        daily = data.get("daily", {})
        if not daily.get("weather_code"):
            return None

        code = daily["weather_code"][0]

        return {
            "condition": _wmo_to_simple(code),
            "description": _wmo_to_condition(code),
            "high_f": daily.get("temperature_2m_max", [None])[0],
            "low_f": daily.get("temperature_2m_min", [None])[0],
            "precipitation_in": daily.get("precipitation_sum", [0])[0],
            "wind_max_mph": daily.get("wind_speed_10m_max", [None])[0],
            "wind_gusts_mph": daily.get("wind_gusts_10m_max", [None])[0],
            "weather_code": code,
            "may_affect_staffing": _may_affect_staffing(code),
        }
    except Exception:
        return None


@st.cache_data(ttl=1800)  # Cache 30 min
def fetch_week_forecast(start_date=None):
    """
    Fetch 7-day forecast for Alma, MI starting from start_date.
    Returns list of daily forecast dicts.
    """
    if start_date is None:
        start_date = date.today()

    from datetime import timedelta
    end_date = start_date + timedelta(days=6)

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": ALMA_LAT,
            "longitude": ALMA_LON,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": ALMA_TIMEZONE,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        forecasts = []

        for i, d in enumerate(dates):
            code = daily["weather_code"][i]
            forecasts.append({
                "date": d,
                "condition": _wmo_to_simple(code),
                "description": _wmo_to_condition(code),
                "high_f": daily["temperature_2m_max"][i],
                "low_f": daily["temperature_2m_min"][i],
                "precipitation_in": daily["precipitation_sum"][i],
                "wind_max_mph": daily["wind_speed_10m_max"][i],
                "weather_code": code,
                "may_affect_staffing": _may_affect_staffing(code),
            })

        return forecasts
    except Exception:
        return []
