from AI.memory_commands import get_memory_plan


COMMAND_KEYWORDS = [
    "open",
    "play",
    "search",
    "remember",
    "launch",
    "close",
    "shutdown",
    "restart",

    "create",
    "write",
    "read",
    "delete",
    "remove",
    "rename",
    "move",
    "copy",
    "save",
    "append"
]

def classify(command):

    if get_memory_plan(command) is not None:
        return "command"

    text = command.lower()

    for word in COMMAND_KEYWORDS:
        if word in text:
            return "command"

    return "chat"
