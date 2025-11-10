"""
get_aqi.py
----------
Fetches PM2.5 air-quality data near given coordinates using OpenAQ (primary)
and AQICN (fallback). Returns weighted average PM2.5 for each coordinate.
"""

import os
import math
import requests
from dotenv import load_dotenv

load_dotenv()

OPENAQ_BASE_URL = "https://api.openaq.org/v3/latest"
AQICN_TOKEN = os.getenv("AQICN_TOKEN")  # Free token from https://aqicn.org/api/

# -----------------------------------
# Utility Functions
# -----------------------------------
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance between two points (in km)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# -----------------------------------
# Primary Source: OpenAQ
# -----------------------------------
def get_pm25_openaq(lat, lon, radius_m=50000, limit=5):
    """
    Fetch PM2.5 near the coordinate using OpenAQ v3.
    Returns weighted average PM2.5 or None if unavailable.
    """
    params = {
        "coordinates": f"{lat},{lon}",
        "radius": radius_m,
        "parameter": "pm25",
        "limit": limit
    }

    try:
        r = requests.get(OPENAQ_BASE_URL, params=params, timeout=15)
        if r.status_code != 200:
            print(f"⚠️ OpenAQ request failed: {r.status_code}")
            return None

        data = r.json().get("results", [])
        if not data:
            return None

        values, weights = [], []
        for item in data:
            measurements = item.get("measurements", [])
            if not measurements:
                continue

            pm = next((m["value"] for m in measurements if m.get("parameter") == "pm25"), None)
            coords = item.get("coordinates")
            if pm is None or not coords:
                continue

            dist = haversine_distance(lat, lon, coords["latitude"], coords["longitude"])
            weight = 1 / (dist + 0.001)
            values.append(pm)
            weights.append(weight)

        if not values:
            return None

        weighted_avg = sum(v * w for v, w in zip(values, weights)) / sum(weights)
        return round(weighted_avg, 2)

    except Exception as e:
        print("⚠️ OpenAQ error:", e)
        return None

# -----------------------------------
# Fallback Source: AQICN
# -----------------------------------
def get_pm25_aqicn(lat, lon):
    """
    Fetch PM2.5 from AQICN as fallback.
    Requires free token from https://aqicn.org/api/.
    """
    if not AQICN_TOKEN:
        return None

    try:
        url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={AQICN_TOKEN}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            print(f"⚠️ AQICN request failed: {r.status_code}")
            return None

        data = r.json()
        if data.get("status") != "ok":
            return None

        pm25 = data["data"]["iaqi"].get("pm25", {}).get("v")
        return round(float(pm25), 2) if pm25 else None

    except Exception as e:
        print("⚠️ AQICN error:", e)
        return None

# -----------------------------------
# Unified Access Function
# -----------------------------------
def get_pm25_nearby(lat, lon):
    """
    Attempts to fetch PM2.5 from OpenAQ first, falls back to AQICN.
    """
    pm = get_pm25_openaq(lat, lon)
    if pm is not None:
        print(f"✅ OpenAQ PM2.5: {pm} µg/m³")
        return pm

    print("⚠️ No data from OpenAQ, trying AQICN...")
    pm = get_pm25_aqicn(lat, lon)
    if pm is not None:
        print(f"✅ AQICN PM2.5: {pm} µg/m³")
        return pm

    print("❌ No air quality data found from either source.")
    return None

# -----------------------------------
# Quick Test
# -----------------------------------
if __name__ == "__main__":
    # Example: Delhi coordinates
    lat, lon = 28.6139, 77.2090
    print("PM2.5 near Delhi:", get_pm25_nearby(lat, lon))
