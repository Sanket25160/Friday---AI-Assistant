import threading

from speech.interrupt import interrupt_event
from speech.wakeword import wait_for_wakeword


def interrupt_loop():
    while True:
        wait_for_wakeword()          # Blocks until "Friday" is detected
        print("Interrupt wake word detected!")
        interrupt_event.set()


def start_interrupt_listener():
    thread = threading.Thread(
        target=interrupt_loop,
        daemon=True
    )
    thread.start()