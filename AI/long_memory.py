import json
import os

FACTS_FILE = "memory/facts.json"


def load():

    if not os.path.exists(FACTS_FILE):
        return {}

    with open(FACTS_FILE, "r") as f:
        return json.load(f)


def save(data):

    with open(FACTS_FILE, "w") as f:
        json.dump(data, f, indent=4)


def remember(key, value):

    data = load()

    data[key] = value

    save(data)


def recall():

    return load()