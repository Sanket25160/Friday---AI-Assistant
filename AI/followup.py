import re
import time
from config import GROQ_API_KEY
from groq import Groq
from speech.speaker import speak_sync
from speech.listener import listen
from tools.browser_agent import read_page, browser_state
from AI.client import answer_from_browser

client = Groq(api_key=GROQ_API_KEY)


def get_followup_suggestion(task, state=None, history=None):
    """
    Analyzes the completed task and current browser/app state to propose
    a relevant follow-up action with a permission question.
    """
    task_lower = (task or "").lower()
    url = (state.get("url", "") if state else "").lower()
    title = (state.get("title", "") if state else "").lower()

    # 1. WhatsApp follow-up
    if "whatsapp" in task_lower or "whatsapp" in url or "whatsapp" in title:
        return {
            "type": "whatsapp",
            "question": "WhatsApp is open. Would you like me to send a message to a contact?",
            "action": "send_whatsapp_message"
        }

    # 2. News channel / portal follow-up
    news_keywords = ["news", "bbc", "cnn", "reuters", "times", "ndtv", "aljazeera", "headline", "hindu", "dainik"]
    if any(k in task_lower or k in url or k in title for k in news_keywords):
        return {
            "type": "news",
            "question": "The news page is open. Would you like me to read out the top headlines?",
            "action": "read_headlines"
        }

    # 3. Shopping / E-commerce search follow-up
    shopping_keywords = ["amazon", "flipkart", "ebay", "sneakers", "shopping", "shoes", "buy", "cart"]
    if any(k in task_lower or k in url for k in shopping_keywords):
        return {
            "type": "shopping",
            "question": "I have loaded the search results. Would you like me to read the top items and prices?",
            "action": "read_products"
        }

    # 4. YouTube follow-up
    if "youtube" in task_lower or "youtube" in url:
        return {
            "type": "youtube",
            "question": "YouTube is open. Would you like me to search for a specific video or play music?",
            "action": "youtube_search"
        }

    # 5. Generic Browser Page (if a webpage is actively open)
    if url and url != "about:blank" and title:
        try:
            prompt = (
                f"The user just asked: \"{task}\".\n"
                f"Currently open webpage: Title=\"{title}\", URL=\"{url}\".\n"
                "Suggest ONE brief, natural question (under 15 words) for Friday to ask the user "
                "proposing a logical next step (e.g. 'Would you like me to ...?').\n"
                "If no further action makes sense, respond with ONLY 'NONE'."
            )
            completion = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=100,
                temperature=0.3
            )
            reply = (completion.choices[0].message.content or "").strip()
            if reply and "NONE" not in reply.upper() and len(reply) < 150:
                # Remove any surrounding quotes
                reply = reply.strip('"\'')
                return {
                    "type": "generic",
                    "question": reply,
                    "action": reply
                }
        except Exception as e:
            print("Follow-up LLM suggestion error:", e)

    return None


def handle_followup_permission(task, state, history, run_agent_func):
    """
    Asks the user for permission to execute a follow-up action and runs it if agreed.
    """
    suggestion = get_followup_suggestion(task, state, history)
    if not suggestion:
        return

    question = suggestion.get("question")
    if not question:
        return

    print(f"\n[Proactive Follow-up] Suggesting: {question}")
    speak_sync(question)

    # Listen for user's decision
    reply = listen()
    if isinstance(reply, dict):
        reply = reply.get("text", "")
    reply = (reply or "").strip()

    if not reply:
        print("[Proactive Follow-up] No response detected. Proceeding to idle.")
        return

    print(f"[Proactive Follow-up] User replied: {reply}")
    reply_lower = reply.lower()

    # Check for decline
    negative_words = ["no", "nope", "don't", "cancel", "never mind", "nevermind", "that's all", "nothing", "stop", "i'm good", "nah"]
    if any(neg in reply_lower for neg in negative_words) and not any(pos in reply_lower for pos in ["yes", "yeah", "sure", "please"]):
        speak_sync("Understood boss.")
        return

    # Execute approved follow-up based on type
    if suggestion["type"] == "news":
        speak_sync("Fetching the top headlines for you now.")
        page_text = read_page()
        if page_text and not page_text.startswith("FAILED"):
            summary = answer_from_browser(
                "Summarize the top 3 to 4 latest headlines from this page clearly and concisely for speech.",
                page_text
            )
            if summary:
                speak_sync(summary)
        else:
            speak_sync("Sorry boss, I couldn't read the headlines on this page.")

    elif suggestion["type"] == "shopping":
        speak_sync("Checking the top results for you.")
        page_text = read_page()
        if page_text and not page_text.startswith("FAILED"):
            summary = answer_from_browser(
                "List the top 3 products with their names and prices concisely for speech.",
                page_text
            )
            if summary:
                speak_sync(summary)
        else:
            speak_sync("Sorry boss, I couldn't read the products on this page.")

    elif suggestion["type"] == "whatsapp":
        # Check if user already provided message details: e.g. "Yes, message Rahul saying hi"
        if any(w in reply_lower for w in ["text", "message", "send", "saying", "tell"]):
            speak_sync("Sending your message on WhatsApp.")
            run_agent_func(f"On WhatsApp, {reply}", allow_followup=False)
        else:
            speak_sync("Who would you like to text and what should I say?")
            msg_details = listen()
            if isinstance(msg_details, dict):
                msg_details = msg_details.get("text", "")
            msg_details = (msg_details or "").strip()
            if msg_details:
                speak_sync("Sending your message.")
                run_agent_func(f"On WhatsApp, send message: {msg_details}", allow_followup=False)
            else:
                speak_sync("No message provided.")

    elif suggestion["type"] == "youtube":
        if any(w in reply_lower for w in ["search", "play", "watch"]):
            run_agent_func(reply, allow_followup=False)
        else:
            speak_sync("What would you like to watch or listen to?")
            yt_query = listen()
            if isinstance(yt_query, dict):
                yt_query = yt_query.get("text", "")
            yt_query = (yt_query or "").strip()
            if yt_query:
                run_agent_func(f"Search YouTube for {yt_query}", allow_followup=False)

    else:
        # Generic suggestion
        affirmative_words = ["yes", "yeah", "sure", "please", "okay", "yep", "do it", "go ahead"]
        if any(aff in reply_lower for aff in affirmative_words):
            if suggestion.get("action"):
                run_agent_func(suggestion["action"], allow_followup=False)
        else:
            # User gave a new specific command
            run_agent_func(reply, allow_followup=False)
