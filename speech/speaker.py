import asyncio
import os
import threading
import time
import edge_tts
import numpy as np
import pygame
import sounddevice as sd
import torch

VOICES = {
    "en": "en-US-JennyNeural",
    "hi": "hi-IN-SwaraNeural"
}

from silero_vad import load_silero_vad, VADIterator
from speech.interrupt import interrupt_event
from speech.language import detect_language

pygame.mixer.init(
    frequency=44100,
    size=-16,
    channels=2,
    buffer=512
)

vad_model = load_silero_vad()


def stop_speaking():
    """Immediately stops Friday from speaking."""
    interrupt_event.set()
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception:
        pass


def _speech_interrupt_monitor(stop_signal):
    """
    Listens to the microphone while audio is playing.
    If the user starts speaking, it stops speech playback immediately.
    """
    samplerate = 16000
    blocksize = 512
    consecutive_speech = 0
    grace_period = 0.35  # seconds after playback starts
    start_time = time.time()

    try:
        with sd.InputStream(
            samplerate=samplerate,
            channels=1,
            dtype="float32",
            blocksize=blocksize,
        ) as stream:
            while not stop_signal.is_set():
                audio, overflowed = stream.read(blocksize)

                # Skip during initial grace period
                if time.time() - start_time < grace_period:
                    continue

                amplitude = np.max(np.abs(audio))
                if amplitude < 0.035:
                    consecutive_speech = 0
                    continue

                audio_tensor = torch.from_numpy(audio.flatten())
                prob = vad_model(audio_tensor, samplerate).item()

                if prob > 0.65:
                    consecutive_speech += 1
                    # Require 2 consecutive frames (~64ms) of detected speech
                    if consecutive_speech >= 2:
                        print("\n[Interrupt: User started speaking!]")
                        stop_speaking()
                        break
                else:
                    consecutive_speech = 0
    except Exception:
        pass


async def speak(text, language="auto"):
    print("Inside speak()")
    interrupt_event.clear()
    filename = "voice.mp3"
    if language == "auto":
        language = detect_language(text)
    voice = VOICES.get(language, VOICES["en"])

    print("Language:", language)
    print("Voice:", voice)

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate="+10%",
        pitch="-2Hz"
    )
    start = time.time()

    await communicate.save(filename)
    print("File exists:", os.path.exists(filename))

    print("Edge-TTS:", time.time() - start)

    print("Speaking...")

    pygame.mixer.music.load(filename)
    print("Loaded:", filename)
    print("Volume:", pygame.mixer.music.get_volume())
    pygame.mixer.music.play()
    print("Play command sent")
    print("Busy immediately:", pygame.mixer.music.get_busy())

    # Start background interrupt monitor while speaking
    stop_signal = threading.Event()
    monitor_thread = threading.Thread(
        target=_speech_interrupt_monitor,
        args=(stop_signal,),
        daemon=True
    )
    monitor_thread.start()

    while True:
        if not pygame.mixer.music.get_busy():
            print("Playback finished")
            break

        if interrupt_event.is_set():
            print("Interrupted!")
            pygame.mixer.music.stop()
            break

        await asyncio.sleep(0.05)

    stop_signal.set()
    if monitor_thread.is_alive():
        monitor_thread.join(timeout=0.2)

    pygame.mixer.music.unload()

    if os.path.exists(filename):
        try:
            os.remove(filename)
        except Exception:
            pass

import time
start = time.time()

def speak_sync(text, language="auto"):
    print("Inside speak_sync")

    def runner():
        asyncio.run(speak(text, language))

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()
