"""
get_routes.py
-------------
Fetches one or more driving route coordinates from OpenRouteService API.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
ORS_API_KEY = os.getenv("ORS_API_KEY")
ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"

def get_route_coordinates(start, end, alternatives=3):
    """
    Fetches up to 'alternatives' route options from OpenRouteService.

    Args:
        start (tuple): (latitude, longitude)
        end (tuple): (latitude, longitude)
        alternatives (int): number of alternate routes

    Returns:
        list of routes, where each route is a list of (lat, lon) tuples
    """
    if not ORS_API_KEY:
        raise RuntimeError("❌ ORS_API_KEY not found. Add it to your .env file.")

    headers = {"Authorization": ORS_API_KEY, "Accept": "application/json, application/geo+json"}
    params = {
        "start": f"{start[1]},{start[0]}",
        "end": f"{end[1]},{end[0]}",
        "alternatives": alternatives
    }

    response = requests.get(ORS_BASE_URL, headers=headers, params=params, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"❌ Failed to fetch route: {response.status_code} — {response.text}")

    data = response.json()

    routes = []
    try:
        for feature in data["features"]:
            coords = [(lat, lon) for lon, lat in feature["geometry"]["coordinates"]]
            routes.append(coords)
    except (KeyError, IndexError):
        raise RuntimeError("Unexpected API response format. Could not parse routes.")

    return routes

# Test
if __name__ == "__main__":
    start = (28.6315, 77.2167)
    end = (28.4595, 77.0266)
    routes = get_route_coordinates(start, end)
    print(f"✅ Retrieved {len(routes)} route(s). First route has {len(routes[0])} points.")
