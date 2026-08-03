from AI.client import ask_chat
from AI.context import set_topic

SYSTEM_PROMPT = """
Extract the main topic from the user's message.

Rules:
- Return ONLY the main topic.
- No explanations.
- No punctuation.
- If there is no obvious topic, return NONE.
"""

def update_topic(message):

    topic = ask_chat(
        message,
        system_prompt=SYSTEM_PROMPT
    ).strip()

    if topic.upper() != "NONE":
        set_topic(topic)

    return topic    