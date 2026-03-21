import json
import os

CONFIG_FILE = "config.json"
DEFAULTS = {
    "music_volume": 0.5
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return DEFAULTS.copy()
    return DEFAULTS.copy()

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def get_music_volume():
    config = load_config()
    return config.get("music_volume", DEFAULTS["music_volume"])

def set_music_volume(vol):
    config = load_config()
    config["music_volume"] = vol
    save_config(config)