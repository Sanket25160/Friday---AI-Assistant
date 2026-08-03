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

    text = command.lower()

    for word in COMMAND_KEYWORDS:
        if word in text:
            return "command"

    return "chat"