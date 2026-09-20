"""Project-relative, atomic JSON storage for Friday's persistent memory."""

import json
import os
from pathlib import Path
import tempfile
from threading import RLock


PROJECT_DIR = Path(__file__).resolve().parents[1]
MEMORY_DIR = PROJECT_DIR / "memory"
memory_lock = RLock()


def read_json(path, expected_type):
    path = Path(path)
    try:
        with path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except FileNotFoundError:
        return expected_type()
    # Never silently replace damaged or incompatible memory with an empty file.
    if not isinstance(data, expected_type):
        raise ValueError(f"Invalid memory format in {path.name}")
    return data


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=path.name + ".", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
