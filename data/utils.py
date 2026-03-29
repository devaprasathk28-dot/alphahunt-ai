import json
import pickle
import os

def save_raw_data(data, filename):
    os.makedirs("data/raw", exist_ok=True)
    with open(f"data/raw/{filename}.json", "w") as f:
        json.dump(data, f)

def save_cache(key, data):
    os.makedirs("data/cache", exist_ok=True)
    with open(f"data/cache/{key}.pkl", "wb") as f:
        pickle.dump(data, f)

def load_cache(key):
    try:
        with open(f"data/cache/{key}.pkl", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None
