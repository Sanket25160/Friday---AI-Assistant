import sounddevice as sd
import torch
import numpy as np
from silero_vad import load_silero_vad, VADIterator
import edge_tts
import pygame
import asyncio
import os
from speech.interrupt import interrupt_event

pygame.mixer.init()

vad_model = load_silero_vad()
vad = VADIterator(vad_model)

def user_started_speaking():

    samplerate = 16000
    blocksize = 512

    with sd.InputStream(
        samplerate=samplerate,
        channels=1,
        dtype="float32",
        blocksize=blocksize,
    ) as stream:

        audio, overflowed = stream.read(blocksize)

        audio_tensor = torch.from_numpy(audio.flatten())

        event = vad(audio_tensor)

        if event is not None:
            print(event)

        return event is not None and "start" in event

async def speak(text):
    interrupt_event.clear()
    filename = "voice.mp3"

    communicate = edge_tts.Communicate(
        text=text,
        voice="en-US-GuyNeural",
        rate="+5%",
        pitch="-2Hz"
    )
    start = time.time()

    await communicate.save(filename)
    print("File exists:", os.path.exists(filename))

    print("Edge-TTS:", time.time() - start)

    print("Speaking...")

    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():

       if interrupt_event.is_set():

           print("Interrupted!")

           pygame.mixer.music.stop()

           interrupt_event.clear()

           break

       await asyncio.sleep(0.05)

    pygame.mixer.music.unload()

    os.remove(filename)

import time
start = time.time()