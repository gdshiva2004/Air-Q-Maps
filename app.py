"""
app.py
------
Air Quality–Aware Route Recommender
-----------------------------------
Uses:
 - GraphHopper Directions API for routes
 - OpenAQ + AQICN for PM2.5 data
 - OpenCage Geocoding for city names (works on Streamlit Cloud)
"""

import streamlit as st
from streamlit_folium import st_folium
from dotenv import load_dotenv
import requests
import os
from src.get_routes import get_route_coordinates
from src.compute_scores import compute_route_metrics
from src.visualize_routes import visualize_route

# -----------------------------------
# Load environment variables
# -----------------------------------
load_dotenv()

# -----------------------------------
# Streamlit Page Config
# -----------------------------------
st.set_page_config(page_title="Air Quality–Aware Route Recommender", layout="wide")

st.title("🌍 Air Quality–Aware Route Recommender")
st.markdown("""
This tool recommends **cleaner routes** by analyzing real-time air quality (PM2.5 levels)
from OpenAQ and AQICN APIs, and calculating a **Healthiness Score** for each route.
""")

# -----------------------------------
# Utility: OpenCage Geocoding
# -----------------------------------
def geocode_city(city):
    """Fetch (lat, lon) using OpenCage API."""
    key = os.getenv("GEOCODER_KEY")
    if not key:
        st.error("⚠️ GEOCODER_KEY not found in .env file.")
        return None

    url = f"https://api.opencagedata.com/geocode/v1/json?q={city}&key={key}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            st.warning(f"⚠️ Geocoding failed for {city}: {r.status_code}")
            return None
        data = r.json()
        if not data["results"]:
            st.warning(f"⚠️ No results found for {city}.")
            return None
        coords = data["results"][0]["geometry"]
        return (coords["lat"], coords["lng"])
    except Exception as e:
        st.error(f"🚨 Geocoding failed for {city}: {e}")
        return None

# -----------------------------------
# Cache route and AQI computations
# -----------------------------------
@st.cache_data(show_spinner=False)
def cached_route(start, end):
    return get_route_coordinates(start, end)

@st.cache_data(show_spinner=False)
def cached_metrics(route_coords, samples):
    return compute_route_metrics(route_coords, sample_count=samples)

# -----------------------------------
# Sidebar Input
# -----------------------------------
st.sidebar.header("⚙️ Input Options")
use_city_names = st.sidebar.checkbox("Enter City Names Instead of Coordinates", value=True)
sample_points = st.sidebar.slider("AQI Sampling Density", 5, 25, 12)
st.sidebar.markdown("---")

# -----------------------------------
# User Input Section
# -----------------------------------
if use_city_names:
    start_city = st.text_input("🏙️ Start Location", "Connaught Place, New Delhi")
    end_city = st.text_input("🏙️ Destination", "Cyber City, Gurgaon")

    if st.button("🚗 Find Route and Analyze Air Quality"):
        st.info("Fetching coordinates via OpenCage Geocoding...")
        start_coords = geocode_city(start_city)
        end_coords = geocode_city(end_city)

        if not start_coords or not end_coords:
            st.error("❌ Could not geocode one or both locations. Try again.")
            st.stop()

        start_lat, start_lon = start_coords
        end_lat, end_lon = end_coords

else:
    st.subheader("Enter Coordinates Manually")
    col1, col2 = st.columns(2)
    with col1:
        start_lat = st.number_input("Start Latitude", value=28.6139)
        start_lon = st.number_input("Start Longitude", value=77.2090)
    with col2:
        end_lat = st.number_input("End Latitude", value=28.4595)
        end_lon = st.number_input("End Longitude", value=77.0266)

    if st.button("🚗 Find Route and Analyze Air Quality"):
        pass

# -----------------------------------
# Route Analysis Section
# -----------------------------------
if 'start_lat' in locals() and 'end_lat' in locals():
    try:
        st.info("Fetching routes and analyzing air quality... Please wait ⏳")

        routes = cached_route((start_lat, start_lon), (end_lat, end_lon))
        if not routes:
            st.error("⚠️ No routes returned from GraphHopper.")
            st.stop()

        st.success(f"✅ Retrieved {len(routes)} possible route(s).")

        route_scores = []
        for i, route_coords in enumerate(routes, 1):
            metrics = cached_metrics(route_coords, samples=sample_points)
            if metrics:
                route_scores.append((i, metrics["healthiness_score"], metrics, route_coords))

        if not route_scores:
            st.error("❌ No AQ data found for this route region.")
            st.stop()

        # Sort by Healthiness Score
        route_scores.sort(key=lambda x: x[1], reverse=True)
        best = route_scores[0]

        st.subheader("🥇 Cleanest Route Summary")
        st.write(f"**Route ID:** {best[0]}")
        st.write(f"**Average PM2.5:** {best[2]['avg_pm25']} µg/m³")
        st.write(f"**Max PM2.5:** {best[2]['max_pm25']} µg/m³")
        st.write(f"**Healthiness Score:** {best[1]}%")

        st.subheader("🗺️ Route Visualization")
        map_obj = visualize_route(best[3], best[2])
        st_folium(map_obj, width=900, height=500)

        if len(route_scores) > 1:
            st.markdown("### 🧾 Comparison of All Routes")
            st.dataframe(
                {
                    "Route ID": [r[0] for r in route_scores],
                    "Avg PM2.5": [r[2]["avg_pm25"] for r in route_scores],
                    "Max PM2.5": [r[2]["max_pm25"] for r in route_scores],
                    "Healthiness Score": [r[1] for r in route_scores],
                }
            )

    except Exception as e:
        st.error(f"🚨 Error occurred: {e}")
