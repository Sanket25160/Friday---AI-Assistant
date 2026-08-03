# from silero_vad import load_silero_vad, VADIterator

# print("Loading model...")

# model = load_silero_vad()

# vad = VADIterator(model)

# print("VAD Iterator loaded successfully!")

from silero_vad import load_silero_vad, VADIterator

model = load_silero_vad()

vad = VADIterator(model)

print(type(vad))
print(dir(vad))