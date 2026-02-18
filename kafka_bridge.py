import json
import os

EVENT_FILE = "../live_event.json"

def read_latest_event():
    if not os.path.exists(EVENT_FILE):
        return None

    with open(EVENT_FILE, "r") as f:
        return json.load(f)
