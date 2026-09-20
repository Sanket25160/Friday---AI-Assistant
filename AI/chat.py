from AI.client import ask_chat
from AI.short_memory import add_turn

SYSTEM_PROMPT = """
You are Friday, a helpful AI assistant.

Answer naturally.

Reply in the same language as the user. Use Hindi when the user writes or
speaks Hindi, and English when the user uses English.

Keep responses concise unless the user asks for detail.
"""

def chat(message):
    # Saved facts and recent turns resolve follow-ups even after a restart,
    # without separate topic-rewriting and extraction API requests.
    response = ask_chat(
        message,
        system_prompt=SYSTEM_PROMPT
    )

    if response.strip():
        add_turn(message, response)

    return response
