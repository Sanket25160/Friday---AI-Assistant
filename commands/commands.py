import webbrowser
import requests
import musicLibrary
from speech.speaker import speak
from AI.client import ask_agent
import asyncio
from config import NEWS_API_KEY
    
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
    else:
        response = ask_agent(c)
        asyncio.run(speak(response))