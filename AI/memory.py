from AI.memory_store import PROJECT_DIR, memory_lock, read_json, write_json

MEMORY_FILE = PROJECT_DIR / "memory.json"


def load_memory():
    with memory_lock:
        return read_json(MEMORY_FILE, list)


def save_memory(memory):
    with memory_lock:
        write_json(MEMORY_FILE, memory)


def remember(task, history):
    with memory_lock:
        memory = load_memory()
        memory.append({"task": task, "history": history})
        save_memory(memory)


def search_memory(query):
    memory = load_memory()

    query = query.lower()

    results = []

    for item in memory:
        if query in item["task"].lower():
            results.append(item)

    return results[-3:]
