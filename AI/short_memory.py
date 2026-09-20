"""Recent conversation context that survives program restarts."""

from AI.memory_store import MEMORY_DIR, memory_lock, read_json, write_json


MEMORY_FILE = MEMORY_DIR / "conversation.json"
MAX_MESSAGES = 20


def get():
    with memory_lock:
        messages = read_json(MEMORY_FILE, list)
    return [
        item for item in messages
        if isinstance(item, dict)
        and item.get("role") in {"user", "assistant"}
        and isinstance(item.get("content"), str)
    ][-MAX_MESSAGES:]


def add(role, content):
    if role not in {"user", "assistant"} or not isinstance(content, str):
        raise ValueError("Invalid conversation message")
    with memory_lock:
        messages = get() + [{"role": role, "content": content}]
        write_json(MEMORY_FILE, messages[-MAX_MESSAGES:])


def add_turn(user_message, assistant_response):
    # Save the complete exchange together, before acknowledging it to the user.
    with memory_lock:
        messages = get() + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_response},
        ]
        write_json(MEMORY_FILE, messages[-MAX_MESSAGES:])


def clear():
    with memory_lock:
        write_json(MEMORY_FILE, [])
