import json
import re
import time
from AI.client import ask_agent
from AI.tools import TOOLS

tool_prompt = ""

for tool in TOOLS:

    params = ", ".join(tool["parameters"])

    tool_prompt += (
        f"- {tool['name']}"
        f"({params}) : "
        f"{tool['description']}\n"
    )

SYSTEM_PROMPT = """
You are Friday.

For every request:

1. Inspect completed actions.
2. Inspect the current browser state.
3. Decide whether any tool is actually needed.
4. Only call tools when necessary.



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
            "tool":"open_website",
            "website":"https://www.google.com"
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

{{ 
    "steps": [
        {{
            "tool": "finish"
        }}
    ]
}}

The conversation includes a section called "Completed actions".

Treat every completed action as already executed.

If a page has already been read and its contents are present in the completed actions, use that information instead of calling read_page again.

If the correct website is already open, do not call open_website again.

If the answer can be produced from previous results:

1. Use the chat tool to answer the user.
2. Then use finish.

Example of recovering from failure:

History

Tool: click_text
Result: FAILED: Element not found

Correct response:

{{
  "steps":[
    {{
      "tool":"type_placeholder",
      "placeholder":"Search",
      "text":"OpenAI"
    }},
    {{
      "tool":"press_enter"
    }}
  ]
}}

{{
  "steps":[
    {{
      "tool":"type_placeholder",
      "placeholder":"Search",
      "text":"OpenAI"
    }},
    {{
      "tool":"press_enter"
    }}
  ]
}}

Planning Rules:

1. Understand the user's final goal before choosing tools.

2. Before calling a tool, check the completed actions.

3. Never repeat a successful tool unless new information is required.

4. If the current browser page already contains the requested information,
   do not navigate elsewhere.

5. If a page has already been read, use the information from history instead
   of calling read_page again.

6. Prefer the minimum number of tool calls.

7. After enough information has been gathered, respond using chat,
   then finish.

8. Only use finish when the user's request has been completely satisfied.

9. If a tool fails, try an alternative approach instead of repeating it forever.

10. Think step-by-step before producing the JSON.

11. When you already know the complete sequence of actions, return all of them in one response.

12. Do not stop after every small browser action.

13. Continue planning until you either:
- need new information from the browser,
- need the result of read_page,
- or the task is complete.

When the task requires reading a webpage and answering about it:
1. open the website if necessary
2. read_page
3. do NOT create a chat step
4. the agent loop will generate the answer from the page
5. finish only after the answer has been generated

Do not repeat completed actions unless something has changed.

Completed actions include both successful and failed tool calls.

If a tool previously returned a result beginning with "FAILED:",
assume the action did not succeed.

Do not repeat the exact same tool call unless something has changed.

Instead, choose another available tool or another strategy.

If a previous chat result summarizes the current page,
use that summary instead of calling read_page again.

Return ONLY valid JSON.
"""

SYSTEM_PROMPT = SYSTEM_PROMPT.format(tool_prompt=tool_prompt)

def decide(command, current_browser=None, history=None, goal=None):

    start = time.perf_counter()

    user_prompt = command

    history_text = ""

    if history:
        history_text = "\nCompleted actions:\n"

        for item in history:

            step = item["action"]
            result = item["result"]

            history_text += (
                f"- Tool: {step['tool']}\n"
                f"  Result: {str(result)[:300]}\n"
                f"  URL: {item.get('url','')}\n"
                f"  Title: {item.get('title','')}\n\n"
            )

    if goal:

        user_prompt += f"""

        =====================
        ORIGINAL GOAL
        =====================

        {goal["task"]}

        The goal has NOT changed.

        Use completed actions to determine what still needs to be done.

        """

    if current_browser:

        user_prompt += f"""

        ====================
        CURRENT BROWSER
        ====================

    Title:
    {current_browser["title"]}

    URL:
    {current_browser["url"]}

    Visible text:
    {current_browser["text"]}
    """

    if history:
        user_prompt += history_text

    print("\n===== USER PROMPT (Preview) =====")
    # print(user_prompt[:500])
    print(user_prompt)

    if len(user_prompt) > 500:
        print("\n... (truncated) ...")

    print("===============================\n")

    print("\n===== HISTORY =====")
    print(history)
    print("===================\n")

    print("\n===== FULL USER PROMPT =====")
    print(user_prompt)
    print("============================\n")

    reply = ask_agent(
        user_prompt,
        system_prompt=SYSTEM_PROMPT
    )

    print("LLM:", time.perf_counter() - start)

    print(reply)

    try:
        reply = (reply or "").strip()

        match = re.search(r"\{.*\}", reply, re.DOTALL)
        if match:
            return json.loads(match.group(0))

        return json.loads(reply)

    except Exception as e:

        print("JSON Error:", e)
        print("Raw reply was:", repr(reply))

        return {
            "steps": [
                {
                    "tool": "chat",
                    "response": "Sorry boss, I didn't understand that."
                }
            ]
        }