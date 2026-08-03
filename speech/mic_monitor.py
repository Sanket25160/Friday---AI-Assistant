import threading

mic_thread = None
running = False


def start():
    global running, mic_thread

    if running:
        return

    running = True

    mic_thread = threading.Thread(
        target=monitor,
        daemon=True
    )

    mic_thread.start()


def stop():
    global running
    running = False


def monitor():

    while running:
        pass