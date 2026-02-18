
import streamlit as st
import random

@st.cache_data
def simulate_positions_cached():
    return simulate_positions()


FLOORS = [6, 7, 8]


def simulate_positions():
    base_lat = 12.964958320625682
    base_lon = 77.71884266137646

    people_positions = []

    for p in st.session_state.people:
        # Small movement
        p["x"] += random.uniform(-1, 1)
        p["y"] += random.uniform(-1, 1)

        # Keep inside building
        p["x"] = max(0, min(100, p["x"]))
        p["y"] = max(0, min(100, p["y"]))

        # Convert to GPS-like coordinates
        lat = base_lat + (p["x"] / 100000)
        lon = base_lon + (p["y"] / 100000)

        people_positions.append({
            "lat": lat,
            "lon": lon,
            "floor": p["floor"],
            "safe": p["safe"]
        })

    return people_positions



def simulate_people():
    if len(st.session_state.people) == 0:
        for i in range(50):
            person = {
                "id": i,
                "floor": random.choice(FLOORS),
                "x": random.uniform(0, 100),
                "y": random.uniform(0, 100),
                "safe": random.choice([True, False])
            }
            st.session_state.people.append(person)

    # Update counts
    st.session_state.safe_count = sum(p["safe"] for p in st.session_state.people)
    st.session_state.unsafe_count = len(st.session_state.people) - st.session_state.safe_count

    # RETURN FLOOR COUNTS ✅
    floor6 = sum(1 for p in st.session_state.people if p["floor"] == 6)
    floor7 = sum(1 for p in st.session_state.people if p["floor"] == 7)
    floor8 = sum(1 for p in st.session_state.people if p["floor"] == 8)

    return {
        "floor6": floor6,
        "floor7": floor7,
        "floor8": floor8,
        "rescued": st.session_state.safe_count
    }
