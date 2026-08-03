import json
import re

from AI.client import ask_agent
from AI.context import get_context, set_topic

FOLLOWUP_WORDS = {
    "he","she","him","her","his","hers",
    "they","them","their",
    "it","its",
    "this","that",
    "former","latter"
}

SYSTEM_PROMPT = """
You extract ONLY the main conversation topic.

Return JSON only.

Example:

{
    "topic":"Albert Einstein"
}

Rules:

If the user explicitly starts talking about another person,
place, movie, object or topic,
return that.

If the user is asking a follow-up question using pronouns
(he, she, it, they...),
return the current topic unchanged.
"""


def update(user_message, assistant_response):

    words = re.findall(r"\b\w+\b", user_message.lower())

    # Don't update on follow-up questions
    if any(word in FOLLOWUP_WORDS for word in words):
        return

    current = get_context()["topic"]

    prompt = f"""
Current topic:
{current}

User:
{user_message}
"""

    reply = ask_agent(
        prompt,
        system_prompt=SYSTEM_PROMPT
    )

    topic = json.loads(reply)["topic"]

    set_topic(topic)

    print("Context:", get_context())