import os
import re
import threading
import time

import numpy as np

from speech.listener import listen

_SOUND_WAKE_COUNT = 2

_WAKE_PHRASES = (
    "friday",
    "wake up",
    "come on get up",
    "hey friday",
)


def contains_wakeword(command):
    if not isinstance(command, str):
        return False
    normalized = " ".join(re.findall(r"[a-z0-9]+", command.lower()))
    return any(
        normalized == phrase or normalized.startswith(phrase + " ")
        or normalized.endswith(" " + phrase)
        or f" {phrase} " in normalized
        for phrase in _WAKE_PHRASES
    )


def is_clap_or_snap(audio, threshold=None):
    """Detect a short, sharp microphone transient such as a clap or snap."""
    if threshold is None:
        threshold = float(os.getenv("FRIDAY_CLAP_THRESHOLD", "0.60"))
    samples = np.asarray(audio, dtype=np.float32).reshape(-1)
    if samples.size == 0:
        return False
    peak = float(np.max(np.abs(samples)))
    rms = float(np.sqrt(np.mean(np.square(samples))))
    hot_samples = np.count_nonzero(np.abs(samples) >= threshold)
    hot_fraction = hot_samples / samples.size
    return (
        peak >= threshold
        and (rms == 0 or peak / rms >= 5.0)
        and hot_fraction <= 0.15
    )


def wait_for_wakeword(cooldown=0.0):

    print("Listening for wake word...")

    # Let the end of a sleep command and confirmation speech leave the mic
    # before listening for a new wake word.
    if cooldown > 0:
        time.sleep(cooldown)

    clap_count = 0
    sequence_started = 0.0
    last_clap = 0.0
    sequence_window = float(os.getenv("FRIDAY_CLAP_WINDOW", "1.0"))
    minimum_gap = float(os.getenv("FRIDAY_CLAP_GAP", "0.15"))
    wake_event = threading.Event()

    def detect_sound(audio):
        nonlocal clap_count, sequence_started, last_clap

        if not is_clap_or_snap(audio):
            return

        now = time.monotonic()
        if now - last_clap < minimum_gap:
            return

        if sequence_started == 0 or now - last_clap > sequence_window:
            clap_count = 0
            sequence_started = now

        clap_count += 1
        last_clap = now
        print(f"Clap or snap detected ({clap_count}/{_SOUND_WAKE_COUNT})")

        if clap_count >= _SOUND_WAKE_COUNT:
            wake_event.set()

    while True:
        command = listen(audio_callback=detect_sound, stop_event=wake_event)
        if isinstance(command, dict):
            if command.get("wake_event"):
                print("Wake event detected: two consecutive claps or snaps")
                return
            command = command.get("text", "")

        print("Wake transcription:", command)
        if contains_wakeword(command):
            print("Wake phrase detected")
            return