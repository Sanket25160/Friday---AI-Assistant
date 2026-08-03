print("Loaded context.py from:", __file__)

context = {
    "topic": None
}

def get_context():
    return context

def set_topic(topic):
    context["topic"] = topic

def update_context(new_topic):
    if new_topic:
        context["topic"] = new_topic


def clear_context():
    context["topic"] = None