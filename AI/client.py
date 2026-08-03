from config import GROQ_API_KEY
from AI.short_memory import add, get
from AI.long_memory import recall
from groq import Groq

client = Groq(
    api_key=GROQ_API_KEY
)


def ask_agent(user_message, system_prompt):

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages.extend(get()[-8:])

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_completion_tokens=120,
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    reply = completion.choices[0].message.content

    # add("user", user_message)
    # add("assistant", reply)

    return reply



# def ask_chat(user_message, system_prompt):

#     messages = [
#         {
#             "role": "system",
#             "content": system_prompt
#         }
#     ]

#     messages.extend(get())

#     messages.append(
#         {
#             "role": "user",
#             "content": user_message
#         }
#     )

#     completion = client.chat.completions.create(
#         model="llama-3.1-8b-instant",
#         messages=messages,
#         max_completion_tokens=500,
#         temperature=0.7
#     )

#     reply = completion.choices[0].message.content

#     add("user", user_message)
#     add("assistant", reply)

#     return reply

import traceback

def ask_chat(user_message, system_prompt):

    print("\n========== ask_agent CALLED ==========")
    print("Message:", user_message)
    traceback.print_stack(limit=5)

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_completion_tokens=500,
        temperature=0.7
    )

    return completion.choices[0].message.content