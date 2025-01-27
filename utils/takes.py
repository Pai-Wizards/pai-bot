import json

from datetime import datetime

from config.settings import TAKES_FILE


def load_takes_json():
    with open(TAKES_FILE, "r") as f:
        return json.load(f)


def save_takes_json(data):
    with open(TAKES_FILE, "w") as f:
        json.dump(data, f)


def days_since_last_take(last_take):
    if last_take is None:
        return 0
    last_take = datetime.fromisoformat(last_take)
    return (datetime.now() - last_take).days
