import time
import threading
from speech.listener import get_model, get_vad
print("Loading speech recognition...")
get_model()
get_vad()
print("Speech recognition ready.")
start = time.perf_counter()

from AI.classifier import classify
from AI.chat import chat

from speech.wakeword import wait_for_wakeword
print("Wakeword:", time.perf_counter() - start)

from speech.listener import listen
print("Listener:", time.perf_counter() - start)

from speech.speaker import speak
print("Speaker:", time.perf_counter() - start)

from AI.agent import decide
print("AI:", time.perf_counter() - start)

from AI.executor import execute
print("Executor:", time.perf_counter() - start)

print("Loading OpenWakeWord...")
# load model
print(f"OpenWakeWord loaded in {time.perf_counter()-start:.2f}s")

print("Loading pygame mixer...")
# load model
print(f"pygame mixer loaded in {time.perf_counter()-start:.2f}s")

print("Loading Faster-Whisper...")
# load model
print(f"Faster-Whisper loaded in {time.perf_counter()-start:.2f}s")

print("Loading Silero-VAD...")
# load model
print(f"Silero-VAD loaded in {time.perf_counter()-start:.2f}s")

import sys
print(sys.executable)
import time
from speech.wakeword import wait_for_wakeword
from speech.listener import listen
import webbrowser
import edge_tts
import pygame
import asyncio
import os
import requests
from groq import Groq
import musicLibrary
from speech.mic_monitor import start
from AI.long_memory import remember
from AI.agent import decide
from AI.executor import execute


from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

NEWS_API_KEY = "40db9d65b01d45d6a066833ec6017d91"

from speech.speaker import speak

from speech.interrupt_listener import start_interrupt_listener

# start_interrupt_listener()

def processCommand(c):
    if "open google" in c.lower():
        webbrowser.open("https://www.google.com")
    elif "open youtube" in c.lower():
        webbrowser.open("https://www.youtube.com")
    elif "open chatgpt" in c.lower():
        webbrowser.open("https://www.chatgpt.com")
    elif "open github" in c.lower():
        webbrowser.open("https://www.github.com")
    elif "open linkedin" in c.lower():
        webbrowser.open("https://www.linkedin.com")
    elif "open instagram" in c.lower():
        webbrowser.open("https://www.instagram.com")
    elif c.lower().startswith("play"):
        song = c.lower().replace("play", "", 1).strip()
        link = musicLibrary.music.get(song)
        if link:
            webbrowser.open(link)
        else:
            asyncio.run(speak("Sorry, I couldn't find that song."))
    elif "news" in c.lower():
        r = requests.get(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}")
        data = r.json()
        articles = data["articles"]
        for article in articles[:5]:
            headline = article["title"]
            asyncio.run(speak(headline))
    
if __name__ == "__main__":
    start() # Start the microphone monitoring in a separate thread
    asyncio.run(speak("Initializing Jarvis..."))
    while True:
        try:
                    wait_for_wakeword()

                    asyncio.run(speak("Yes boss, how may I help you?"))                 

                    #Initialize timer as soon as the wake word is detected
                    last_command_time = time.time()
                    
                    while True:
                    
                        command = listen()

                        if not command:
                            if time.time() - last_command_time > 8:
                                asyncio.run(speak("Going back to sleep."))
                                break
                            continue

                        last_command_time = time.time()

                        print("Command:", command)

                        intent = classify(command)

                        print("Intent:", intent)

                        if intent == "command":
                            print(">>> USING DECIDE()")
                            plan = decide(command)
                            print(plan)

                            for action in plan["steps"]:
                                execute(action)

                            print("Execute finished")

                        elif intent == "chat":
                            print(">>> USING CHAT()")
                            response = chat(command)

                            print("Response:", response)
                            asyncio.run(speak(response))

                        else:

                            print(f"Unknown intent: {intent}")

                            asyncio.run(
                                speak("Sorry boss, I couldn't understand what you wanted.")
                            )

        except Exception:
            import traceback
            traceback.print_exc()

