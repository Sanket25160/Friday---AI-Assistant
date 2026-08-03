import json
import os

MEMORY_FILE = "memory/conversation.json"

# Load memory from file
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        conversation = json.load(f)
else:
    conversation = []


def save():
    with open(MEMORY_FILE, "w") as f:
        json.dump(conversation, f, indent=4)


def add(role, content):
    conversation.append({
        "role": role,
        "content": content
    })

    # Keep only the last 20 messages
    if len(conversation) > 20:
        conversation.pop(0)

    save()


def get():
    return conversation


def clear():
    conversation.clear()
    save()