"""Durable facts, loaded from disk whenever Friday needs them."""

from AI.memory_store import MEMORY_DIR, memory_lock, read_json, write_json


FACTS_FILE = MEMORY_DIR / "facts.json"


def load():
    with memory_lock:
        return read_json(FACTS_FILE, dict)


def save(data):
    with memory_lock:
        write_json(FACTS_FILE, data)


def remember(key, value):
    if not isinstance(key, str) or not key.strip():
        raise ValueError("A memory needs a nonempty key")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("A memory needs a nonempty value")
    key, value = key.strip().casefold(), value.strip()
    with memory_lock:
        data = load()
        # Preserve existing facts and update the same key on corrections.
        existing = next((k for k in data if k.casefold() == key), key)
        data[existing] = value
        save(data)
    return f"I'll remember: {value}" if key.startswith("note:") else f"I'll remember your {key}: {value}"


def recall():
    return load()


def describe_memory():
    facts = recall()
    if not facts:
        return "I haven't saved any facts yet. Say remember that, followed by what you want me to save."
    entries = [
        str(value) if key.startswith("note:") else f"{key}: {value}"
        for key, value in facts.items()
    ]
    return "Here's what I remember: " + "; ".join(entries)
