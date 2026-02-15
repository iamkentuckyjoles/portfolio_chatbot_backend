import requests, time
from django.core.cache import cache
from django.conf import settings
from datetime import datetime

LAT, LON = 11.2135, 124.3921  # Villaba, Leyte
CACHE_KEY = "villaba_weather"
CACHE_TIMEOUT = 60 * 60  # 1 hour
RATE_KEY = "villaba_weather_rate"
RATE_LIMIT = 1  # max 1 call per hour

def can_call_api():
    calls = cache.get(RATE_KEY, [])
    now = time.time()
    # keep only calls in last hour
    calls = [c for c in calls if now - c < 3600]
    if len(calls) >= RATE_LIMIT:
        return False
    calls.append(now)
    cache.set(RATE_KEY, calls, 3600)
    return True

def get_weather():
    # check cache first
    data = cache.get(CACHE_KEY)
    if data:
        return data

    # enforce rate limit
    if not can_call_api():
        return cache.get(CACHE_KEY) or {"error": "Rate limit exceeded"}

    # call OpenWeatherMap
    url = (
        f"https://api.openweathermap.org/data/2.5/weather?"
        f"lat={LAT}&lon={LON}&appid={settings.OPENWEATHERMAP_API_KEY}&units=metric"
    )
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return {"error": f"Weather API call failed: {str(e)}"}

    # store in cache
    cache.set(CACHE_KEY, data, CACHE_TIMEOUT)
    return data

def format_weather(data):
    # current timestamp split into date and time
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    # handle error cases gracefully
    if "error" in data:
        return {
            "location": "Villaba, Leyte, Philippines",
            "temp": None,
            "description": None,
            "message": data["error"],
            "date": current_date,
            "time": current_time,
        }

    condition = data["weather"][0]["main"]
    description = data["weather"][0]["description"]
    temp = data["main"]["temp"]

    # Default message
    message = "Coding regardless of the weather."

    if condition == "Clear":
        message = "Perfect weather for building cool apps."
    elif condition == "Rain":
        message = "Rainy day, coding mode activated."
    elif condition == "Thunderstorm":
        message = "Storm outside, but shipping features inside."
    elif condition == "Clouds":
        message = "Cloudy skies, clear code."
    elif condition == "Drizzle":
        message = "Light rain, heavy productivity."

    return {
        "location": "Villaba Leyte, Philippines",
        "temp": temp,
        "description": description,
        "message": message,
        "date": current_date,
        "time": current_time,
    }
