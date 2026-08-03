from AI.client import ask_chat
from AI.context import get_context
from AI.context_updater import update
from AI.context_rewriter import rewrite

SYSTEM_PROMPT = """
You are Jarvis, a helpful AI assistant.

Answer naturally.

Keep responses concise unless the user asks for detail.
"""

FOLLOWUP_WORDS = {
    "he",
    "she",
    "him",
    "her",
    "his",
    "hers",
    "they",
    "them",
    "their",
    "it",
    "its",
    "this",
    "that",
    "former",
    "latter"
}


def chat(message):

    import re

    words = re.findall(r"\b\w+\b", message.lower())

    if any(word in FOLLOWUP_WORDS for word in words):
      message = rewrite(
          message,
          get_context()["topic"]
      )

      print("Rewritten:", message)

    # Always ask the chat model
    response = ask_chat(
        message,
        system_prompt=SYSTEM_PROMPT
    )

    # Update context after getting the response
    update(
        user_message=message,
        assistant_response=response
    )

    return response