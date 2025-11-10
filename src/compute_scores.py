"""
compute_scores.py
-----------------
Combines route coordinates with AQI data to compute overall pollution exposure metrics.
"""

from src.get_aqi import get_pm25_nearby

def sample_route_points(route_coords, max_samples=20):
    """Samples a subset of coordinates to reduce API load."""
    n = len(route_coords)
    if n == 0:
        return []
    step = max(1, n // max_samples)
    return route_coords[::step]

def compute_route_metrics(route_coords, sample_count=20):
    """Compute average PM2.5, max PM2.5, and healthiness score for a route."""
    sampled_points = sample_route_points(route_coords, sample_count)
    pm_values = []

    print(f"🔍 Sampling {len(sampled_points)} points along the route...")

    for lat, lon in sampled_points:
        pm = get_pm25_nearby(lat, lon)
        if pm:
            pm_values.append(pm)

    if not pm_values:
        print("⚠️ No air quality data found for this route.")
        return None

    avg_pm = sum(pm_values) / len(pm_values)
    max_pm = max(pm_values)
    pollution_score = 0.7 * avg_pm + 0.3 * max_pm
    healthiness_score = max(0, 100 - (pollution_score / 5))

    return {
        "avg_pm25": round(avg_pm, 2),
        "max_pm25": round(max_pm, 2),
        "pollution_score": round(pollution_score, 2),
        "healthiness_score": round(healthiness_score, 2),
        "samples_used": len(pm_values)
    }
