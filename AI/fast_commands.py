"""Recognize a small set of complete commands without an LLM request.

This module only builds plans. Unrecognized or potentially compound requests
return None so that the normal planner can interpret the entire instruction.
"""

import re
from AI.memory_commands import get_memory_plan


_WEBSITES = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "chatgpt": "https://www.chatgpt.com",
    "github": "https://www.github.com",
    "linkedin": "https://www.linkedin.com",
    "instagram": "https://www.instagram.com",
    "whatsapp": "https://web.whatsapp.com",
    "whatsapp web": "https://web.whatsapp.com",
    "bbc": "https://www.bbc.com",
}

# False negatives are intentional: these words can introduce another action.
# Even a legitimate search for "open source" can use the regular planner.
_COMPOUND_QUERY = re.compile(
    r"\b(?:and|or|then|after|before|also|next|instead|please|"
    r"but|only|with|without|while|when|if|unless|until|once|"
    r"open|read|tell|show|click|visit|go|play|write|create|save|close|"
    r"stop|send|type|press|download|delete|summarize|summarise|"
    r"translate|explain|give|return|sort|filter|compare|select|get|find|"
    r"launch|remember|remove|rename|move|copy|append|list|check)\b",
    re.IGNORECASE,
)


def get_fast_plan(task):
    """Return a complete plan for an exact simple command, otherwise None.

    Supported forms: ``open SITE``, ``close [the] browser``, and
    ``search Google/YouTube for QUERY``. Leading/trailing "please", variable
    spaces, letter case, and terminal speech punctuation are ignored. Search
    queries retain their case and are limited to plain words, spaces, +, #,
    and hyphens; quotes, conditions, compound instructions, and sentences use
    the planner.
    """
    memory_plan = get_memory_plan(task)
    if memory_plan is not None:
        return memory_plan

    if not isinstance(task, str) or "\n" in task or "\r" in task:
        return None

    command = task.strip().rstrip(".!?").strip()
    command = re.sub(r"^please,?\s+", "", command, flags=re.IGNORECASE)
    command = re.sub(r",?\s+please$", "", command, flags=re.IGNORECASE)
    command = " ".join(command.split())

    match = re.fullmatch(r"open (.+)", command, flags=re.IGNORECASE)
    if match:
        website = _WEBSITES.get(match.group(1).lower())
        if website:
            return _complete_plan({"tool": "open_website", "website": website})
        return None

    if re.fullmatch(r"close (?:the )?browser", command, flags=re.IGNORECASE):
        return _complete_plan({"tool": "close_browser"})

    match = re.fullmatch(
        r"search (google|youtube) for (.+)", command, flags=re.IGNORECASE
    )
    if match:
        query = match.group(2)
        if (
            not re.fullmatch(r"[\w+# -]+", query)
            or not re.search(r"[^\W_]", query)
            or _COMPOUND_QUERY.search(query)
        ):
            return None
        return _complete_plan({
            "tool": "search_" + match.group(1).lower(),
            "query": query,
        })

    return None


def _complete_plan(action):
    return {"steps": [action, {"tool": "finish"}]}
