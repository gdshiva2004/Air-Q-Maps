"""
visualize_routes.py
-------------------
Displays route on Folium map with pollution metrics.
"""

import folium
from folium.plugins import BeautifyIcon

def route_color(pm25):
    if pm25 is None:
        return "gray"
    if pm25 < 50:
        return "green"
    if pm25 < 100:
        return "orange"
    if pm25 < 200:
        return "red"
    return "darkred"

def visualize_route(coords, metrics, out_file="data/route_map.html"):
    if not coords:
        raise ValueError("No coordinates to visualize")

    avg_pm = metrics.get("avg_pm25")
    color = route_color(avg_pm)
    center = coords[len(coords)//2]

    m = folium.Map(location=center, zoom_start=12)
    folium.PolyLine(coords, color=color, weight=6, opacity=0.8).add_to(m)

    folium.Marker(coords[0], tooltip="Start",
                  icon=BeautifyIcon(icon_shape="marker", border_color="blue")).add_to(m)
    folium.Marker(coords[-1], tooltip="End",
                  icon=BeautifyIcon(icon_shape="marker", border_color="red")).add_to(m)

    info = (
        f"<b>Average PM2.5:</b> {metrics.get('avg_pm25')} µg/m³<br>"
        f"<b>Max PM2.5:</b> {metrics.get('max_pm25')} µg/m³<br>"
        f"<b>Healthiness Score:</b> {metrics.get('healthiness_score')}%"
    )
    folium.Marker(center, popup=info).add_to(m)
    m.save(out_file)
    return m
