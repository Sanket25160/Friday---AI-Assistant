import webbrowser
import urllib.parse

WEBSITES = {
    "google": "https://google.com",
    "youtube": "https://youtube.com",
    "chatgpt": "https://chatgpt.com",
    "github": "https://github.com",
    "linkedin": "https://linkedin.com",
    "instagram": "https://instagram.com",
}

def search_youtube(query):
    url = (
        "https://www.youtube.com/results?search_query="
        + urllib.parse.quote(query)
    )
    webbrowser.open(url)

def open_website(name):
    webbrowser.open(f"https://{name}.com")

def search_google(query):
    url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    webbrowser.open(url)


def open_google():
    webbrowser.open("https://www.google.com")


def open_youtube():
    webbrowser.open("https://www.youtube.com")


def open_chatgpt():
    webbrowser.open("https://chatgpt.com")


def open_github():
    webbrowser.open("https://github.com")


def open_linkedin():
    webbrowser.open("https://linkedin.com")


def open_instagram():
    webbrowser.open("https://instagram.com")