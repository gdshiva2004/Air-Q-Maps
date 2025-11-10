"""
get_routes.py
-------------
Fetches driving routes using the GraphHopper Directions API.
Fully compatible replacement for OpenRouteService.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
GRAPH_KEY = os.getenv("GRAPH_KEY")

GRAPH_API = "https://graphhopper.com/api/1/route"

def get_route_coordinates(start, end, alternatives=1):
    """
    Fetches route coordinates between start and end points using GraphHopper API.

    Args:
        start (tuple): (latitude, longitude)
        end (tuple): (latitude, longitude)
        alternatives (int): number of alternate routes (GraphHopper free plan supports 1)

    Returns:
        list of routes, where each route is a list of (lat, lon) tuples
    """
    if not GRAPH_KEY:
        raise RuntimeError("❌ GRAPH_KEY not found. Add it to your .env file.")

    params = {
        "point": [f"{start[0]},{start[1]}", f"{end[0]},{end[1]}"],
        "vehicle": "car",
        "locale": "en",
        "points_encoded": False,
        "key": GRAPH_KEY
    }

    try:
        response = requests.get(GRAPH_API, params=params, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"❌ Failed to fetch route: {response.status_code} — {response.text}")

        data = response.json()

        # Extract route coordinates
        routes = []
        paths = data.get("paths", [])
        if not paths:
            raise RuntimeError("⚠️ No route found in GraphHopper response.")

        for path in paths[:alternatives]:
            coords = [(p[1], p[0]) for p in path["points"]["coordinates"]]  # lon, lat → lat, lon
            routes.append(coords)

        return routes

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"⚠️ Network error while fetching route: {e}")

if __name__ == "__main__":
    # Test example
    start = (28.6315, 77.2167)  # Connaught Place, Delhi
    end = (28.4595, 77.0266)    # Cyber City, Gurgaon
    routes = get_route_coordinates(start, end)
    print(f"✅ Retrieved {len(routes)} route(s). First route has {len(routes[0])} points.")
