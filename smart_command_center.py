
import streamlit as st
from streamlit_folium import st_folium
import folium
import matplotlib.pyplot as plt
import numpy as np
import os, time, random

# Your modules
from kafka_bridge import read_latest_event
from data_simulator import simulate_people, simulate_positions_cached
from shared_state import get_latest_event, init_state

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Aptiv Smart Emergency Command Center", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(BASE_DIR, "assets", "building_layout.png")
BLINKIT_LOGO = "https://upload.wikimedia.org/wikipedia/commons/2/2b/Blinkit_logo.png"

# ---------------- INIT STATE ----------------
init_state()

if "people_initialized" not in st.session_state:
    simulate_people()
    st.session_state.people_initialized = True

# ---------------- EMERGENCY DEMO FLAG ----------------
if "demo_emergency" not in st.session_state:
    st.session_state.demo_emergency = False

# ---------------- AMBULANCE GPS ----------------
if "ambulance_lat" not in st.session_state:
    st.session_state.ambulance_lat = 12.9645
    st.session_state.ambulance_lon = 77.7180

def move_ambulance():
    st.session_state.ambulance_lat += 0.00001
    st.session_state.ambulance_lon += 0.00001

# ---------------- AUTO REFRESH ----------------
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

if "last_update" not in st.session_state:
    st.session_state.last_update = 0

REFRESH_INTERVAL = 3

if st.session_state.auto_refresh:
    if time.time() - st.session_state.last_update > REFRESH_INTERVAL:
        st.session_state.last_update = time.time()
        st.rerun()

# ---------------- EVENT DATA ----------------
event_data = read_latest_event() or {}
severity = event_data.get("severity", "NONE")
action = event_data.get("action", "Idle")
event = get_latest_event() or {}

# Demo Override
if st.session_state.demo_emergency:
    event["emergency"] = True
    severity = "CRITICAL"
    action = "🔥 Fire detected Floor 7 | Evacuate via Exit B"

# ---------------- SIDEBAR ----------------
st.sidebar.subheader("🔄 Refresh Control")

if st.sidebar.button("▶ Start Live Refresh"):
    st.session_state.auto_refresh = True

if st.sidebar.button("⏸ Stop Refresh"):
    st.session_state.auto_refresh = False

if st.sidebar.button("🔁 Manual Refresh"):
    st.rerun()

st.sidebar.write(f"Auto Refresh: {'ON' if st.session_state.auto_refresh else 'OFF'}")

# ---- Judge Demo Buttons ----
st.sidebar.subheader("🚨 Judge Demo Controls")

if st.sidebar.button("🔥 Trigger Emergency Scenario"):
    st.session_state.demo_emergency = True

if st.sidebar.button("✅ Reset to Normal Mode"):
    st.session_state.demo_emergency = False

# ---------------- FUNCTIONS ----------------
def show_floor_map(floor):
    people = [p for p in st.session_state.people if p["floor"] == floor]
    fig, ax = plt.subplots(figsize=(4,4))

    if people:
        x = [p["x"] for p in people]
        y = [p["y"] for p in people]
        colors = ["green" if p["safe"] else "red" for p in people]
        ax.scatter(x, y, c=colors)

    ax.set_title(f"Floor {floor} Live Tracking")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.grid(True)
    st.pyplot(fig)

def show_heatmap():
    people = st.session_state.people
    if not people:
        return
    x = [p["x"] for p in people]
    y = [p["y"] for p in people]
    heatmap, _, _ = np.histogram2d(x, y, bins=25)

    fig, ax = plt.subplots(figsize=(6,4))
    ax.imshow(heatmap.T, origin='lower')
    ax.set_title("🔥 Crowd Density Heatmap")
    st.pyplot(fig)

# ---------------- HEADER ----------------
st.title("🚨 Aptiv Smart Emergency Command Center")
st.caption("Live AI-driven Emergency Monitoring Dashboard")

# Emergency Banner
if st.session_state.demo_emergency:
    st.error("🚨🚨 LIVE EMERGENCY SIMULATION ACTIVE 🚨🚨")
    st.warning("Fire detected | AI evacuation activated | Ambulance dispatched")

# ---------------- KPIs ----------------
st.subheader("📊 Live Emergency KPIs")

people_data = {
    "Floor 6": sum(p["floor"] == 6 for p in st.session_state.people),
    "Floor 7": sum(p["floor"] == 7 for p in st.session_state.people),
    "Floor 8": sum(p["floor"] == 8 for p in st.session_state.people),
}

total_people = len(st.session_state.people)
rescued = st.session_state.safe_count
unsafe = st.session_state.unsafe_count

col1, col2, col3, col4 = st.columns(4)
col1.metric("👥 Total Occupants", total_people)
col2.metric("✅ Rescued", rescued)
col3.metric("❌ Unsafe", unsafe)

if event.get("emergency"):
    col4.metric("🚨 Emergency", "YES", delta="CRITICAL", delta_color="inverse")
else:
    col4.metric("🚨 Emergency", "NO")

st.divider()

# ---------------- MAIN LAYOUT ----------------
left, right = st.columns([2.5, 1])

# ================================================= LEFT PANEL =================================================
with left:
    # -------- DIGITAL TWIN MAP --------
    st.subheader("🗺️ Digital Twin Live Map")

    base_lat, base_lon = 12.9649583, 77.7188426
    m = folium.Map(location=[base_lat, base_lon], zoom_start=20)

    # Exits
    folium.Marker([base_lat-0.00003, base_lon], popup="Exit A", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker([base_lat, base_lon+0.00003], popup="Exit B", icon=folium.Icon(color="green")).add_to(m)

    # People
    for p in simulate_positions_cached() or []:
        folium.CircleMarker(
            [p["lat"], p["lon"]],
            radius=4,
            color="green" if p["safe"] else "red",
            fill=True
        ).add_to(m)

    # Ambulance
    if event.get("emergency"):
        move_ambulance()
        folium.Marker(
            [st.session_state.ambulance_lat, st.session_state.ambulance_lon],
            popup="🚑 Ambulance Enroute",
            icon=folium.Icon(color="red", icon="ambulance", prefix="fa")
        ).add_to(m)

    st_folium(m, height=450, width=900)
    st.divider()

    # -------- HEATMAP --------
    st.subheader("🔥 Crowd Density Heatmap")
    show_heatmap()
    st.divider()

    # -------- FLOOR TRACKING --------
    st.subheader("🏢 Floor Tracking")
    st.bar_chart(people_data)
    floor = st.selectbox("Select Floor View", [6,7,8])
    show_floor_map(floor)
    st.divider()

    # -------- AI EVACUATION --------
    st.subheader("🧠 AI Evacuation Planner")

    if event.get("emergency"):
        st.error("🔥 Fire detected near Exit A")
        st.warning("⚠ Exit A Blocked")
        st.success("➡ AI Route: Corridor C → Staircase 2 → Exit B")
    else:
        st.success("✅ No Emergency Detected")

# ================================================= RIGHT PANEL =================================================
with right:
    # -------- BUILDING LAYOUT --------
    st.subheader("🏢 Building Layout")
    if os.path.exists(IMAGE_PATH):
        st.image(IMAGE_PATH, width=350)
    else:
        st.warning("Building layout image missing")

    st.divider()

    # -------- CAMERA FEED --------
    st.subheader("🎥 Live Camera Feed (Demo)")
    st.video("https://www.youtube.com/watch?v=LZNZnxCOq0I&pp=ygUaY2FtZXJhIGZlZWQgZm9yIGVhcnRocXVha2U%3D")  # demo CCTV stream

    st.divider()

    # -------- EMERGENCY ALERTS --------
    st.subheader("🚑 Command Center Alerts")

    if severity == "CRITICAL":
        st.error("🔥 CRITICAL EMERGENCY DETECTED")
    elif severity == "HIGH":
        st.warning("⚠ High Risk Situation")
    else:
        st.success("✅ Normal")

    if event.get("emergency"):
        st.error("🚑 Ambulance Auto Dispatched")
        st.write(f"AI Action: {action}")

    # -------- BLINKIT INSTANT AMBULANCE DEMO --------
    st.divider()
    st.subheader("⚡ Instant Ambulance Service")

    colA, colB = st.columns([1,2])
    with colA:
        st.image("data:image/png;base64,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", width=80)

    with colB:
        if st.button("🚑 Call Blinkit Ambulance API (Demo)"):
            st.success("Blinkit API Triggered - Ambulance booked in 90 seconds!")

    # -------- HOSPITAL CONTACTS --------
    st.divider()
    st.subheader("🏥 Nearby Hospitals")

    st.write("""
    **Facility Emergency Contact:** +91-99999-11111  
    **Apollo Hospital:** 2.3 km  
    **Manipal Hospital:** 4.1 km  
    **Columbia Asia Hospital:** 3.5 km  
    """)

    # -------- TWILIO SMS/CALL DEMO --------
    st.divider()
    st.subheader("📲 Real Emergency Notifications (Twilio)")

    if st.button("📩 Send Real SMS Alert"):
        st.info("Twilio SMS Triggered (Integrate API Keys in backend)")

    if st.button("📞 Trigger Emergency Call"):
        st.info("Twilio Call Triggered")

# ================================================= END =================================================
