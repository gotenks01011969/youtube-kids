import os
from datetime import datetime


YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "")

groqcloud_key_source = os.getenv("GROQCLOUD_KEYS") or os.getenv("GROQCLOUD_API_KEY", "")

groqcloud_keys = [
    key.strip()
    for key in groqcloud_key_source.split(",")
    if key.strip()
]

def get_current_day():
    # Get the current day of the week (0 = Monday, 6 = Sunday)
    current_day_index = datetime.today().weekday()  # Monday=0, Sunday=6
    current_day_index = (current_day_index + 1) % 7
    return current_day_index

def get_groqcloud_key():
    if not groqcloud_keys:
        raise RuntimeError("Set GROQCLOUD_API_KEY or GROQCLOUD_KEYS.")
    return groqcloud_keys[get_current_day() % len(groqcloud_keys)]
