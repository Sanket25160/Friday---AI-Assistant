import re


_SLEEP_PHRASES = (
    "go to sleep",
    "go back to sleep",
    "sleep",
    "take a rest",
    "i will see you later",
    "see you later",
    "you can go",
    "bye bye",
    "bye",
    "i am going",
    "i am going now",
)


def is_sleep_command(command):
    """Return True when speech explicitly asks Friday to stop listening."""
    if not isinstance(command, str):
        return False

    normalized = re.sub(r"[^a-z0-9]+", " ", command.lower()).strip()
    return normalized in _SLEEP_PHRASES or normalized in {
        f"please {phrase}" for phrase in _SLEEP_PHRASES
    }