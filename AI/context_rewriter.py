import json

from AI.client import ask_agent

SYSTEM_PROMPT = """
You rewrite follow-up questions.

Current topic:
...

User:
...

Rules:

1. Rewrite ONLY if the user refers to the current topic using pronouns like:
he
she
him
her
his
hers
they
them
their
it
its
this person
that person

2. If the user explicitly mentions another person, place, object or topic,
DO NOT rewrite anything.

3. If the user starts a new topic, return the original sentence unchanged.

4. If the sentence already contains a proper noun (for example Mahatma Gandhi,
Isaac Newton, Japan, One Piece), do not rewrite it.

Return ONLY JSON.

Example:

{
    "rewritten":"When was Albert Einstein born?"
}
"""

def rewrite(message, current_topic):

    prompt = f"""
Current topic:
{current_topic}

User:
{message}
"""

    reply = ask_agent(
        prompt,
        system_prompt=SYSTEM_PROMPT
    )

    # result = json.loads(reply)

    # return result["rewritten"]

    result = json.loads(reply)

    print("DEBUG:", result)
    print("DEBUG TYPE:", type(result["rewritten"]))

    return result["rewritten"]