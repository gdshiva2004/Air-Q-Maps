"""
app.py
------
Air Quality–Aware Route Recommender (Final Version)
---------------------------------------------------
Features:
✅ City name input (Geopy)
✅ Route caching & AQI caching
✅ Multiple route ranking by healthiness
✅ Folium map visualization inside Streamlit
"""

import streamlit as st
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from src.get_routes import get_route_coordinates
from src.compute_scores import compute_route_metrics
from src.visualize_routes import visualize_route

# -----------------------------------
# Streamlit App Config
# -----------------------------------
st.set_page_config(page_title="Air Quality Route Recommender", layout="wide")

st.title("🌍 Air Quality–Aware Route Recommender")
st.markdown("""
This tool recommends **cleaner routes** by analyzing real-time air quality (PM2.5 levels)
from the OpenAQ API and calculating a **Healthiness Score** for each route.
""")

# -----------------------------------
# Utility Functions (Cached)
# -----------------------------------
@st.cache_data(show_spinner=False)
def cached_route(start, end):
    """Cache route API calls."""
    return get_route_coordinates(start, end)

@st.cache_data(show_spinner=False)
def cached_metrics(route_coords, samples):
    """Cache AQI computation results."""
    return compute_route_metrics(route_coords, sample_count=samples)

# -----------------------------------
# User Input Section
# -----------------------------------
st.sidebar.header("⚙️ Input Options")

use_city_names = st.sidebar.checkbox("Enter City Names Instead of Coordinates", value=True)
sample_points = st.sidebar.slider("AQI Sampling Density", 5, 25, 12)
st.sidebar.markdown("---")

if use_city_names:
    geolocator = Nominatim(user_agent="aq_route_app")
    start_city = st.text_input("🏙️ Start Location", "Connaught Place, Delhi")
    end_city = st.text_input("🏙️ Destination", "Cyber City, Gurgaon")

    start_lat = start_lon = end_lat = end_lon = None

    if st.button("🚗 Find Route and Analyze Air Quality"):
        with st.spinner("Geocoding locations..."):
            start_loc = geolocator.geocode(start_city)
            end_loc = geolocator.geocode(end_city)

        if not start_loc or not end_loc:
            st.error("❌ Could not find one or both locations. Try adjusting names.")
        else:
            start_lat, start_lon = start_loc.latitude, start_loc.longitude
            end_lat, end_lon = end_loc.latitude, end_loc.longitude
else:
    st.subheader("Enter Coordinates")
    col1, col2 = st.columns(2)
    with col1:
        start_lat = st.number_input("Start Latitude", value=28.6315)
        start_lon = st.number_input("Start Longitude", value=77.2167)
    with col2:
        end_lat = st.number_input("End Latitude", value=28.4595)
        end_lon = st.number_input("End Longitude", value=77.0266)

    if st.button("🚗 Find Route and Analyze Air Quality"):
        pass  # We'll handle below

# -----------------------------------
# Route & AQI Analysis
# -----------------------------------
if start_lat and end_lat:
    try:
        st.info("Fetching routes and analyzing air quality... Please wait ⏳")

        routes = cached_route((start_lat, start_lon), (end_lat, end_lon))
        if not routes:
            st.error("⚠️ No routes returned from OpenRouteService.")
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

        # Sort by healthiness (higher is cleaner)
        route_scores.sort(key=lambda x: x[1], reverse=True)
        best = route_scores[0]

        st.subheader("🥇 Cleanest Route Summary")
        st.write(f"**Route ID:** {best[0]}")
        st.write(f"**Average PM2.5:** {best[2]['avg_pm25']} µg/m³")
        st.write(f"**Max PM2.5:** {best[2]['max_pm25']} µg/m³")
        st.write(f"**Healthiness Score:** {best[1]}%")

        # Visualization
        st.subheader("🗺️ Route Visualization")
        map_obj = visualize_route(best[3], best[2])
        st_folium(map_obj, width=900, height=500)

        # Table for all routes
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
