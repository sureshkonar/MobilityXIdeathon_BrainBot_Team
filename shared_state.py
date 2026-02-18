
import streamlit as st

def init_state():
    if "people" not in st.session_state:
        st.session_state.people = []

    if "safe_count" not in st.session_state:
        st.session_state.safe_count = 0

    if "unsafe_count" not in st.session_state:
        st.session_state.unsafe_count = 0

    if "latest_event" not in st.session_state:
        st.session_state.latest_event = {
            "severity": "NORMAL",
            "message": "No emergency detected",
            "emergency": False
        }

def update_event(event):
    st.session_state.latest_event = event

def get_latest_event():
    return st.session_state.latest_event