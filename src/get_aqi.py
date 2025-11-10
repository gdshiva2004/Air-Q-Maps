"""
get_aqi.py
----------
Fetches recent PM2.5 air-quality data near a given coordinate using OpenAQ v3 API.
"""

import requests
import math

OPENAQ_BASE_URL = "https://api.openaq.org/v3/latest"

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_pm25_nearby(lat, lon, radius_m=50000, limit=5):
    """
    Returns weighted average PM2.5 (µg/m³) near the coordinate.
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
        print("⚠️ AQ fetch error:", e)
        return None

if __name__ == "__main__":
    lat, lon = 28.6315, 77.2167  # Delhi
    print("PM2.5 near Delhi:", get_pm25_nearby(lat, lon))
