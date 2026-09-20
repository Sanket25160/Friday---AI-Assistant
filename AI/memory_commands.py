"""Build local plans for explicit memories and simple profile statements."""

import hashlib
import re


_COMPOUND = re.compile(
    r"(?:\b(?:and|then|also|but)\s+(?:then\s+)?|[.!?,]\s+)"
    r"(?:please\s+)?(?:open|launch|search|play|read|write|create|delete|close|"
    r"send|tell|show|click|type|press|save|remember|forget|summarize)\b",
    re.IGNORECASE,
)


def get_memory_plan(message):
    if not isinstance(message, str):
        return None
    text = message.strip().rstrip(".!?").strip()
    text = re.sub(r"^please,?\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r",?\s+please$", "", text, flags=re.IGNORECASE)
    if _COMPOUND.search(text) or "\n" in text or "\r" in text or ";" in text:
        return None

    if text.casefold() in {
        "what do you remember", "what do you remember about me",
        "show my memories", "show my saved memories", "list my memories",
    }:
        return _plan({"tool": "recall_memory"})

    if "?" in message or re.search(r"\b(?:if|unless)\b", text, re.IGNORECASE):
        return None
    explicit = re.fullmatch(r"(?:remember|keep in mind)\b(.*)", text, flags=re.IGNORECASE)
    fact = explicit.group(1).strip() if explicit else text
    if explicit:
        fact = re.sub(r"^(?:that|this)\b", "", fact, flags=re.IGNORECASE).lstrip(" :")
        if not fact:
            return None

    # Only unambiguous declarations are captured automatically. Other facts
    # can always be saved verbatim using an explicit 'remember that' request.
    match = re.fullmatch(
        r"my (name|city|profession|birthday|favorite color|favourite color|"
        r"favorite food|favourite food|preferred language) is (.+)", fact, flags=re.IGNORECASE,
    )
    if match and not re.search(r"[.!?;]|\b(?:and|not|or)\b", match.group(2), re.IGNORECASE):
        key = match.group(1).casefold().replace("favourite", "favorite")
        return _plan({"tool": "remember_fact", "key": key, "value": match.group(2).strip()})

    for pattern, key in ((r"I live in (.+)", "city"), (r"I work as (?:an? )?(.+)", "profession")):
        match = re.fullmatch(pattern, fact, flags=re.IGNORECASE)
        if match and not re.search(r"[.!?;]|\b(?:and|not|or)\b", match.group(1), re.IGNORECASE):
            return _plan({"tool": "remember_fact", "key": key, "value": match.group(1).strip()})

    if explicit:
        # Repeated notes use the same key, while distinct notes are retained.
        normalized = " ".join(fact.casefold().split())
        key = "note:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
        return _plan({"tool": "remember_fact", "key": key, "value": fact})
    return None


def _plan(action):
    return {"steps": [action, {"tool": "finish"}]}
