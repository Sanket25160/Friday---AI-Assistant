from collections import deque
from speech.state import interrupt_event
from silero_vad import load_silero_vad, VADIterator
from faster_whisper import WhisperModel
import numpy as np
import sounddevice as sd
import wave
import os
import torch
import threading
model = None
model_lock = threading.Lock()

def get_model():
    global model

    if model is None:
        with model_lock:
            if model is None:
                print("Loading Faster-Whisper...")
                model = WhisperModel(
                    "base",
                    device="cpu",
                    compute_type="int8"
                )
                print("Loaded!")

    return model

vad = None

def get_vad():
    global vad

    if vad is None:
        print("Loading Silero VAD...")

        vad_model = load_silero_vad()

        vad = VADIterator(
            vad_model,
            min_silence_duration_ms=400
        )

        print("Silero VAD loaded!")

    return vad

#Converting audio to text using Faster-Whisper

def listen():
    return listen_vad()

def listen_vad():

    model = get_model()
    vad = get_vad()
    print("Listening for command...")
    print("Waiting for speech...")
    vad.reset_states()

    print("Starting VAD listener...")

    samplerate = 16000
    blocksize = 512

    with sd.InputStream(
        samplerate=samplerate,
        channels=1,
        dtype="float32",
        blocksize=blocksize,
    ) as stream:

        frames = []
        recording = False

        pre_buffer = deque(maxlen=8)

        while True:

            audio, overflowed = stream.read(blocksize)

            pre_buffer.append(audio.copy())
            
            audio_tensor = torch.from_numpy(audio.flatten())

            event = vad(audio_tensor)

            if event is not None:
                print(event)

            if event is not None and "start" in event:
                print("Recording started")
                recording = True
                frames.extend(pre_buffer)

            if recording:
                frames.append(audio.copy())

            if event is not None and "end" in event:
                print("Recording finished")
                break

        if len(frames) == 0:
            return ""

        audio_data = np.concatenate(frames, axis=0)

        print(f"Frames recorded: {len(frames)}")

        audio_int16 = (audio_data * 32767).astype(np.int16)

        filename = "temp.wav"

        with wave.open(filename, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)      # 16-bit audio
            wf.setframerate(samplerate)
            wf.writeframes(audio_int16.tobytes())

        import time

        start_time = time.time()

        segments, info = model.transcribe(
            filename,
            language="en"
        )
        
        print("Whisper:", time.time() - start_time)

        text = ""

        for segment in segments:
            text += segment.text

        os.remove(filename)

        return text.strip()

def test_stream():
    samplerate = 16000
    blocksize = 512

    print("Opening microphone...")

    with sd.InputStream(
        samplerate=samplerate,
        channels=1,
        dtype="float32",
        blocksize=blocksize,
    ) as stream:

        print("Microphone opened!")

        while True:
            
            audio, overflowed = stream.read(blocksize)

            volume = np.max(np.abs(audio))
            print(f"Volume: {volume:.4f}")