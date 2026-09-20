from collections import deque
from speech.state import interrupt_event
from silero_vad import load_silero_vad, VADIterator
from faster_whisper import WhisperModel
import numpy as np
import sounddevice as sd
import torch
import threading
import time
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

def listen(audio_callback=None, stop_event=None):
    return listen_vad(audio_callback=audio_callback, stop_event=stop_event)

def listen_vad(audio_callback=None, stop_event=None):

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

            if audio_callback is not None:
                audio_callback(audio)

            if stop_event is not None and stop_event.is_set():
                return {"text": "", "wake_event": True}

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

    # The microphone can close before decoding. Whisper accepts the 16 kHz
    # mono waveform directly, so there is no need for a temporary WAV file.
    audio_data = np.ascontiguousarray(
        np.concatenate(frames, axis=0).reshape(-1), dtype=np.float32
    )

    duration = len(audio_data) / samplerate

    print(f"Recording duration: {duration:.2f} seconds")

    if duration < 1.0:
        print("Recording too short. Ignoring.")
        return ""

    print(f"Frames recorded: {len(frames)}")

    start_time = time.perf_counter()
    segments, info = model.transcribe(audio_data)

    # Faster-Whisper decodes lazily while its segments are consumed.
    text = "".join(segment.text for segment in segments).strip()
    print("Whisper:", time.perf_counter() - start_time)

    detected_language = info.language

    print("Detected language:", detected_language)
    print("Command:", text)

    return {
        "text": text,
        "language": detected_language
    }

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
