import json
import os

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "music_volume": 1.0,
    "background": "bg1",
    "snow_enabled": True
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
        except (json.JSONDecodeError, IOError):
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False


def get_music_volume():
    config = load_config()
    # Округляем при загрузке — защита от старых "кривых" значений в конфиге
    vol = config.get("music_volume", DEFAULT_CONFIG["music_volume"])
    return round(max(0.0, min(1.0, float(vol))), 2)


def set_music_volume(volume):
    config = load_config()
    # Округляем до 2 знаков — чтобы не было 1.3877787807814457e-16
    config["music_volume"] = round(max(0.0, min(1.0, float(volume))), 2)
    save_config(config)


def get_background():
    config = load_config()
    return config.get("background", DEFAULT_CONFIG["background"])


def set_background(bg_key):
    config = load_config()
    config["background"] = bg_key
    save_config(config)


def get_snow_enabled():
    config = load_config()
    return config.get("snow_enabled", DEFAULT_CONFIG["snow_enabled"])


def set_snow_enabled(enabled):
    config = load_config()
    config["snow_enabled"] = enabled
    save_config(config)


def get_all_settings():
    return load_config()


def reset_config():
    save_config(DEFAULT_CONFIG)