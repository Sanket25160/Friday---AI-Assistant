import json
import time
from AI.client import ask_agent
from AI.tools import TOOLS

import os

from tools.browser_agent import browser_state

print("USING AGENT FILE:", os.path.abspath(__file__))

tool_prompt = ""

for tool in TOOLS:

    params = ", ".join(tool["parameters"])

    tool_prompt += (
        f"- {tool['name']}"
        f"({params}) : "
        f"{tool['description']}\n"
    )

SYSTEM_PROMPT = """
You are Jarvis.

Available tools:

{tool_prompt}

Always return ONE JSON object.

The JSON must contain a list called "steps".

Use the tool exactly as described, including all required parameters.

Use ONLY the available tools listed above.

Never invent tool names.

If no suitable tool exists, use chat.

Example:

{{
    "steps":[
        {{
            "tool":"open_google"
        }}
    ]
}}

Example:

{{
    "steps":[
        {{
            "tool":"play_song",
            "song":"Believer"
        }}
    ]
}}

{{
    "steps":[
        {{
            "tool":"open_application",
            "application":"chrome"
        }},
        {{
            "tool":"open_youtube"
        }}
    ]
}}

{{
    "steps":[
        {{
            "tool":"create_file",
            "filename":"notes.txt"
        }}
    ]
}}

{{
    "steps":[
        {{
            "tool":"write_file",
            "filename":"notes.txt",
            "content":"Hello World"
        }}
    ]
}}

{{
    "steps":[
        {{
            "tool":"read_file",
            "filename":"notes.txt"
        }}
    ]
}}

Return ONLY valid JSON.
"""

SYSTEM_PROMPT = SYSTEM_PROMPT.format(tool_prompt=tool_prompt)

print(SYSTEM_PROMPT)

def decide(command, browser_state=None):

    print(">>> decide() CALLED")

    start = time.perf_counter()

    user_prompt = command

    if browser_state:

        user_prompt += f"""

    Current browser:

    Title:
    {browser_state["title"]}

    URL:
    {browser_state["url"]}

    Visible text:
    {browser_state["text"]}
    """

    reply = ask_agent(
        user_prompt,
        system_prompt=SYSTEM_PROMPT
    )

    print("LLM:", time.perf_counter() - start)

    print(reply)

    try:
        reply = reply.strip()

        if reply.startswith("```"):
            reply = reply.replace("```json", "")
            reply = reply.replace("```", "")
            reply = reply.strip()

        return json.loads(reply)

    except Exception as e:

        print("JSON Error:", e)

        return {
            "steps": [
                {
                    "tool": "chat",
                    "response": "Sorry boss, I didn't understand that."
                }
            ]
        }