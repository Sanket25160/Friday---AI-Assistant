import os
import re
import shutil
import subprocess

APPS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "vs code": "code",
    "notepad": "notepad",
    "calculator": "calc",
    "paint": "mspaint",
    "command prompt": "cmd",
    "file explorer": "explorer",
}

def open_application(app_name):
    if not isinstance(app_name, str) or not app_name.strip():
        return False

    requested = app_name.strip()
    app_name = requested.lower()

    executable = APPS.get(app_name)
    if executable is None:
        executable = requested if os.path.isfile(requested) else shutil.which(requested)

    if executable is not None:
        subprocess.Popen([executable])
        return True

    # Windows' Start command can resolve registered GUI applications that are
    # not on PATH. Reject shell metacharacters before passing the user input on.
    if os.name == "nt" and not re.search(r"[&|<>^\"\n\r]", requested):
        subprocess.Popen(["cmd.exe", "/c", "start", "", requested])
        return True

    return False