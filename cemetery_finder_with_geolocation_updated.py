
import streamlit as st
import pandas as pd
import folium
from math import radians, cos, sin, asin, sqrt
from streamlit.components.v1 import html

# Try importing streamlit_folium, handle if not available
try:
    from streamlit_folium import st_folium
    folium_available = True
except ImportError:
    folium_available = False

# Load cemetery data
df = pd.read_csv("cemeteries.csv")

# Haversine formula to calculate distance between two lat/lon points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    return R * c

# Streamlit UI
st.title("Closest Cemetery Finder in London")
st.write("This app detects your location and finds the nearest cemetery from the database.")

# JavaScript to get geolocation
geolocation_script = """
<script>
navigator.geolocation.getCurrentPosition(
    (position) => {
        const coords = position.coords.latitude + "," + position.coords.longitude;
        window.parent.postMessage(coords, "*");
    },
    (err) => {
        window.parent.postMessage("error", "*");
    }
);
</script>
"""

# Display the script and capture the result
location = st.empty()
coords = st.empty()

with location:
    html(geolocation_script, height=0)

user_lat = None
user_lon = None

# Listen for the coordinates from the browser
coords_value = st.query_params.get("coords", [None])[0]

if coords_value:
    try:
        user_lat, user_lon = map(float, coords_value.split(","))
    except:
        st.error("Could not parse location.")
else:
    # Use JavaScript to capture coordinates and reload with query params
    html("""
    <script>
    window.addEventListener("message", (event) => {
        if (event.data && event.data !== "error") {
            const coords = event.data;
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.set("coords", coords);
            window.location.href = newUrl.toString();
        }
    });
    </script>
    """, height=0)

# If coordinates are available, calculate and display the closest cemetery
if user_lat is not None and user_lon is not None:
    df["Distance_km"] = df.apply(lambda row: haversine(user_lat, user_lon, row["Latitude"], row["Longitude"]), axis=1)
    closest = df.loc[df["Distance_km"].idxmin()]

    st.subheader("Closest Cemetery")
    st.write(f"**Name**: {closest['Name']}")
    st.write(f"**Borough**: {closest['Borough']}")
    st.write(f"**Type**: {closest['Type']}")
    st.write(f"**Year Established**: {closest['Year_Established']}")
    st.write(f"**Distance**: {closest['Distance_km']:.2f} km")

    if folium_available:
        st.subheader("Map View")
        m = folium.Map(location=[user_lat, user_lon], zoom_start=12)
        folium.Marker([user_lat, user_lon], tooltip="Your Location", icon=folium.Icon(color="blue")).add_to(m)
        folium.Marker([closest["Latitude"], closest["Longitude"]], tooltip=closest["Name"], icon=folium.Icon(color="green")).add_to(m)
        st_folium(m, width=700, height=500)
    else:
        st.warning("Map view requires the 'streamlit-folium' package. Please install it using 'pip install streamlit-folium'.")
else:
    st.info("Waiting for location permission...")
