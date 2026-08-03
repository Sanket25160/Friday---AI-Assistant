# from pathlib import Path

# def create_file(filename):

#     path = Path(filename)

#     path.touch(exist_ok=True)

#     return f"{filename} created successfully."

from pathlib import Path

def create_file(filename):
    path = Path(filename)

    print("Creating file at:", path.resolve())   # <-- add this

    path.touch(exist_ok=True)

    return f"File created: {filename}"

def write_file(filename, content):

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    return f"Wrote to {filename}"

def read_file(filename):

    with open(filename, "r", encoding="utf-8") as f:
        return f.read()