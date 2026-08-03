import json

from AI.client import ask_agent

MEMORY_PROMPT = """
You decide whether a user's message contains a personal fact worth remembering.

Remember ONLY stable personal facts like:

- name
- age
- city
- profession
- hobbies
- favorite things
- preferences
- goals

Do NOT remember:

- Questions
- Temporary requests
- Commands
- Greetings
- Random chat

Return ONLY JSON.

If nothing should be remembered:

{
    "remember": false
}

If something should be remembered:

{
    "remember": true,
    "key": "...",
    "value": "..."
}
"""


def analyze(user_message):

    reply = ask_agent(
        user_message,
        system_prompt=MEMORY_PROMPT
    )

    return json.loads(reply)