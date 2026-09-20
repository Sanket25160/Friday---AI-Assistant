import os
import re
import time

from speech.speaker import speak_sync

from tools.browser_agent import (
    open_website,
    search_google,
    search_youtube,
    read_page,
    get_links,
    click_text,
    scroll_page,
    zoom_page,
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
from AI.long_memory import remember as remember_fact, describe_memory
from tools.applications import open_application


def open_desktop_application(app_name):
    try:
        if open_application(app_name):
            return f"Opened {app_name}"
        return f"FAILED: Could not find application {app_name}"
    except Exception as e:
        return f"FAILED: Could not open {app_name}: {e}"


# ============================================================
# REMOVE URLs FROM SPEECH
# ============================================================

def clean_for_speech(text):

    if not isinstance(text, str):
        return text

    # Remove http:// and https:// URLs
    text = re.sub(
        r'https?://\S+',
        '',
        text
    )

    # Remove www. URLs
    text = re.sub(
        r'www\.\S+',
        '',
        text
    )

    # Remove excessive whitespace
    text = re.sub(
        r'\s+',
        ' ',
        text
    ).strip()

    return text


# ============================================================
# SPEAK NEWS
# ============================================================

def speak_news():

    articles = get_news()

    for article in articles:

        title = article.get("title", "")

        if title:
            speak_sync(
                clean_for_speech(title)
            )


# ============================================================
# TOOLS
# ============================================================

TOOLS = {

    "remember_fact":
        lambda action: remember_fact(action["key"], action["value"]),

    "recall_memory":
        lambda action: describe_memory(),

    "search_google":
        lambda action:
        search_google(action["query"]),

    "open_website":
        lambda action:
        open_website(action["website"]),

    "open_application":
        lambda action:
        open_desktop_application(action["application"]),

    "search_youtube":
        lambda action:
        search_youtube(action["query"]),

    "create_file":
        lambda action:
        create_file(action["filename"]),

    "write_file":
        lambda action:
        write_file(
            action["filename"],
            action["content"]
        ),

    "read_file":
        lambda action:
        read_file(action["filename"]),

    "read_page":
        lambda action:
        read_page(),

    "finish":
        lambda action:
        "DONE",

    "get_links":
        lambda action:
        get_links(),

    "click_text":
        lambda action:
        click_text(action["text"]),

    "scroll_page":
        lambda action:
        scroll_page(action.get("direction", "down"), action.get("amount", 600)),

    "zoom_page":
        lambda action:
        zoom_page(action.get("direction", "in"), action.get("amount", 10)),

    "type_placeholder":
        lambda action:
        type_placeholder(
            action["placeholder"],
            action["text"]
        ),

    "press_enter":
        lambda action:
        press_enter(),

    "close_browser":
        lambda action:
        close_browser(),

    "play_song":
        lambda action:
        play_song(action["song"]),

    "speak_news":
        lambda action:
        speak_news(),

    "chat":
        lambda action:
        action["response"],
}


# ============================================================
# EXECUTE TOOL
# ============================================================

def execute(action, announce=True):
    """Execute an action, optionally skipping intermediate status speech."""

    print("\n========== EXECUTE CALLED ==========")
    print("ACTION:", action)

    tool = action.get("tool")

    if tool is None:
        return "FAILED: No tool specified"

    if tool == "finish":
        return "DONE"

    if tool not in TOOLS:

        speak_sync(
            "I don't know how to do that yet."
        )

        return "FAILED: Unknown tool"

    print("Executing tool...")

    try:

        # ----------------------------------------------------
        # Execute actual tool
        # ----------------------------------------------------

        started = time.perf_counter()
        result = TOOLS[tool](action)
        print(f"[Latency] Tool {tool}: {time.perf_counter() - started:.2f}s")

        # ----------------------------------------------------
        # Finish
        # ----------------------------------------------------

        if result == "DONE":
            return "DONE"

        print("Result:", result)

        # ----------------------------------------------------
        # CHAT RESPONSE
        # ----------------------------------------------------

        if tool == "chat":

            print(
                "Calling speak_sync for chat..."
            )

            speech_text = clean_for_speech(
                result
            )

            if speech_text:
                speak_sync(speech_text)

        # ----------------------------------------------------
        # NORMAL TOOL RESPONSE
        # ----------------------------------------------------

        elif (
            isinstance(result, str)
            and result.strip()
            and tool != "read_page"
            and (announce or tool in {"read_file", "recall_memory"} or result.startswith("FAILED"))
        ):

            speech_text = clean_for_speech(
                result
            )

            if speech_text:
                speak_sync(speech_text)

        print("Tool execution finished")

        return result

    except Exception as e:

        import traceback

        traceback.print_exc()

        return f"FAILED: {str(e)}"
