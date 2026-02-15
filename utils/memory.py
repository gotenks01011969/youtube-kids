import json
import os
from utils.logger import logger

MEMORY_DIR = "memory"
PUBLISHED_FILE = f"{MEMORY_DIR}/published_videos.json"
RECENT_TOPICS_FILE = f"{MEMORY_DIR}/recent_topics.json"
RECENT_FORMATS_FILE = f"{MEMORY_DIR}/recent_formats.json"

MAX_RECENT_TOPICS = 20
MAX_RECENT_FORMATS = 5

def _load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)

def _save(path, data):
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ---------- READERS ----------

def get_recent_topics():
    return _load(RECENT_TOPICS_FILE, [])

def get_recent_formats():
    return _load(RECENT_FORMATS_FILE, [])

# ---------- VALIDATORS ----------

def is_topic_new(topic: str) -> bool:
    return topic not in get_recent_topics()

def is_format_allowed(format_name: str) -> bool:
    recent = get_recent_formats()
    return not recent or recent[-1] != format_name

# ---------- WRITERS ----------

def record_video(topic: str, format_name: str):
    topics = get_recent_topics()
    formats = get_recent_formats()

    topics.append(topic)
    formats.append(format_name)

    topics = topics[-MAX_RECENT_TOPICS:]
    formats = formats[-MAX_RECENT_FORMATS:]

    _save(RECENT_TOPICS_FILE, topics)
    _save(RECENT_FORMATS_FILE, formats)

    logger.info("Memory updated")
