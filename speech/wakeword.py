import numpy as np
import sounddevice as sd

import openwakeword
from openwakeword.model import Model

openwakeword.utils.download_models()

model = None

def get_model():
    global model

    if model is None:
        print("Loading OpenWakeWord...")

        model = Model(
            inference_framework="onnx",
            wakeword_models=["hey_jarvis"]
        )

        print("OpenWakeWord loaded!")

    return model


def wait_for_wakeword():

    model = get_model()
    
    samplerate = 16000
    blocksize = 1280

    print("Listening for wake word...")

    with sd.InputStream(
        samplerate=samplerate,
        channels=1,
        dtype="int16",
        blocksize=blocksize,
    ) as stream:

        while True:

            audio, overflowed = stream.read(blocksize)

            audio = audio.flatten()

            prediction = model.predict(audio)

            if prediction["hey_jarvis"] > 0.5:
                print("Wake word detected!")
                return