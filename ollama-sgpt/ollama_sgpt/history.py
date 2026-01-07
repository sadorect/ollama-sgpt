import json
import os

def load_history(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

def save_history(path, history):
    with open(path, "w") as f:
        json.dump(history, f, indent=2)
