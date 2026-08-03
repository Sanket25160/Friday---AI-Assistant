from unittest import result

from tools.browser_agent import (
    open_website,
    search_google,
    search_youtube,
    read_page,
    get_links,
    click_text,
    type_placeholder,
    press_enter,
    close_browser,
)

from tools.files import (
    create_file,
    write_file,
    read_file,
) 

from tools.music import play_song
from tools.news import get_news
from speech.speaker import speak
import asyncio

TOOLS = {
    "search_google": lambda action: search_google(action["query"]),
    "open_website": lambda action: open_website(action["website"]),
    "search_youtube": lambda action: search_youtube(action["query"]),
    "search_google": lambda action: search_google(action["query"]),
    "create_file": lambda action: create_file(action["filename"]),
    "write_file": lambda action: write_file(action["filename"], action["content"]),
    "read_file": lambda action: read_file(action["filename"]),
    "read_page": lambda action: read_page(),

    "get_links": lambda action: get_links(),

    "click_text": lambda action: click_text(action["text"]),

    "type_placeholder": lambda action:
        type_placeholder(
            action["placeholder"],
            action["text"]
        ),

    "press_enter": lambda action: press_enter(),

    "close_browser": lambda action: close_browser(),

    "play_song": lambda action: play_song(action["song"]),
    "speak_news": lambda action: speak_news(),
    "chat": lambda action: asyncio.run(speak(action["response"])),
}

def speak_news():
    articles = get_news()

    for article in articles:
        asyncio.run(speak(article["title"]))

def execute(action):

    print("Executor recieved:", action)

    tool = action.get("tool")

    if tool is None:
        return

    if tool not in TOOLS:
        asyncio.run(
            speak(
                "I don't know how to do that yet."
            )
        )
        return
    
    print("Executing tool...")

    try:
        result = TOOLS[tool](action)

        if isinstance(result, str):
            asyncio.run(speak(result))

        print("Result:", result)

        if isinstance(result, str) and result.strip():
            asyncio.run(speak(result))

        print("Tool execution finished")

    except Exception as e:
        import traceback
        traceback.print_exc()