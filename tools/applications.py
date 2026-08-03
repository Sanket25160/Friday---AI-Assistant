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
    app_name = app_name.lower()

    if app_name not in APPS:
        return False

    subprocess.Popen(APPS[app_name])
    return True