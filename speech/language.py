import re


def detect_language(text):
    """Return the speech language code for supported assistant voices."""
    if not isinstance(text, str) or not text.strip():
        return "en"

    devanagari = len(re.findall(r"[\u0900-\u097f]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    if devanagari and devanagari >= latin * 0.1:
        return "hi"
    return "en"