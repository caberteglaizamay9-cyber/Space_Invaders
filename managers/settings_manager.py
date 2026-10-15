import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "sound_volume": 80,
    "music_enabled": True,
    "sound_enabled": True,
    "mobile_controls": False,
    "graphics": "high",
}


def load_settings():
    """Nag-load sa mga setting gikan sa settings.json file."""
    if not os.path.exists(SETTINGS_FILE):
        save_settings(dict(DEFAULT_SETTINGS))
        return dict(DEFAULT_SETTINGS)

    try:
        with open(SETTINGS_FILE, "r") as file:
            data = json.load(file)

        settings = dict(DEFAULT_SETTINGS)
        settings.update(data)
        return settings

    except (json.JSONDecodeError, IOError, TypeError, ValueError):
        return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    """Nag-save sa mga bag-ong setting ngadto sa settings.json file."""
    try:
        with open(SETTINGS_FILE, "w") as file:
            json.dump(settings, file, indent=4)
    except IOError as e:
        print(f"Error sa pag-save: {e}")