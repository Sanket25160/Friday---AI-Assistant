import os
import sys
import time
from pathlib import Path
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ============================================================
# PLAYWRIGHT GLOBALS
# ============================================================

_playwright = None
browser = None
context = None
page = None


# ============================================================
# START / RESTART BROWSER
# ============================================================

def start_browser():
    global _playwright, browser, context, page

    print("\n========== STARTING BROWSER ==========")

    # Close previous browser
    try:
        if context:
            context.close()
        elif browser:
            browser.close()
    except Exception:
        pass

    # Stop previous Playwright
    try:
        if _playwright:
            _playwright.stop()
    except Exception:
        pass

    _playwright = sync_playwright().start()

    user_data_dir = os.getenv("FRIDAY_BROWSER_USER_DATA_DIR")
    if not user_data_dir:
        user_data_dir = str(
            Path(os.getenv("LOCALAPPDATA", Path.home()))
            / "Google" / "Chrome" / "User Data"
        )
    profile = os.getenv("FRIDAY_BROWSER_PROFILE", "Default")

    try:
        context = _playwright.chromium.launch_persistent_context(
            user_data_dir,
            channel="chrome",
            headless=False,
            args=[f"--profile-directory={profile}"],
        )
        browser = None
        print(f"Using Chrome profile: {profile}")
    except Exception as persistent_error:
        # A running Chrome process can lock its profile. Keep browser tasks
        # available with a temporary context and explain why login is absent.
        print("Could not open the persistent Chrome profile:", persistent_error)
        browser = _playwright.chromium.launch(headless=False)
        context = browser.new_context()

    page = context.new_page()

    print("Browser started successfully.")

    return page


# ============================================================
# ENSURE BROWSER IS ALIVE
# ============================================================

def ensure_browser():

    global page

    # Browser has never been started
    if page is None:
        return start_browser()

    # Check if page is still alive
    try:
        page.title()
        return page

    except Exception:
        print("Browser/page was closed.")
        print("Trying to recreate browser...")

        return start_browser()


# ============================================================
# CHECK WHETHER BROWSER EXISTS
# ============================================================

def browser_is_running():

    global page

    if page is None:
        return False

    try:
        page.title()
        return True

    except Exception:
        return False


# ============================================================
# OPEN WEBSITE
# ============================================================

def open_website(website):

    page = ensure_browser()

    if not website.startswith(("http://", "https://")):
        website = "https://" + website

    print(f"Opening: {website}")

    try:

        page.goto(
            website,
            wait_until="domcontentloaded",
            timeout=30000
        )

        print(f"Opened {page.url}")

        return f"Opened {page.url}"

    except Exception as e:

        print("Open website failed:", e)

        return f"FAILED: {str(e)}"


# ============================================================
# SEARCH GOOGLE
# ============================================================

def search_google(query):

    global page

    page = ensure_browser()

    query = query.strip()

    url = (
        "https://www.google.com/search?q="
        + quote_plus(query)
    )

    print("Google search:", query)

    try:

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000
        )

        print(f"Google opened: {page.url}")

        return f"Searched Google for {query}"

    except Exception as e:

        print("Google search error:", e)

        return f"FAILED: Google search failed: {e}"


# ============================================================
# SEARCH YOUTUBE
# ============================================================

def search_youtube(query):

    global page

    page = ensure_browser()

    query = query.strip()

    url = (
        "https://www.youtube.com/results?search_query="
        + quote_plus(query)
    )

    print("YouTube search:", query)

    try:

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000
        )

        print(f"YouTube opened: {page.url}")

        return f"Searched YouTube for {query}"

    except Exception as e:

        print("YouTube search error:", e)

        return f"FAILED: YouTube search failed: {e}"


# ============================================================
# READ PAGE
# ============================================================

def read_page():

    page = ensure_browser()

    try:

        page.wait_for_load_state(
            "domcontentloaded",
            timeout=10000
        )

    except Exception:
        pass

    try:

        text = page.locator("body").inner_text()

        safe_text = text.encode(
            "utf-8",
            errors="replace"
        ).decode("utf-8")

        print("\n========== PAGE CONTENT ==========")
        print(safe_text[:5000])
        print("==================================\n")

        return text

    except Exception as e:

        print("Read page failed:", e)

        return f"FAILED: {str(e)}"


# ============================================================
# BROWSER STATE
# ============================================================

def browser_state(include_text=True):

    global page

    # IMPORTANT:
    # Do NOT start a browser just to obtain state.

    if page is None:

        return {
            "title": "",
            "url": "",
            "text": ""
        }

    try:

        title = page.title()

        return {
            "title": title,
            "url": page.url,
            "text": page.locator("body").inner_text() if include_text else ""
        }

    except Exception as e:

        print("Browser state failed:", e)

        return {
            "title": "",
            "url": "",
            "text": ""
        }


# ============================================================
# GET LINKS
# ============================================================

def get_links():

    global page

    page = ensure_browser()

    try:

        links = page.locator("a").all()

        results = []

        for link in links:

            try:

                text = link.inner_text().strip()
                href = link.get_attribute("href")

                if text and href:

                    results.append({
                        "text": text,
                        "href": href
                    })

            except Exception:
                continue

        return results

    except Exception as e:

        print("Get links error:", e)

        return f"FAILED: {e}"


# ============================================================
# CLICK TEXT
# ============================================================

def click_text(text):

    global page

    page = ensure_browser()

    try:

        locator = page.get_by_text(
            text,
            exact=True
        ).first

        locator.click(
            timeout=10000
        )

        time.sleep(2)

        return f"Clicked {text}"

    except Exception as e:

        print("Click error:", e)

        return (
            f"FAILED: Could not click {text}: {e}"
        )


def scroll_page(direction="down", amount=600):
    page = ensure_browser()

    try:
        pixels = abs(float(amount))
        if str(direction).lower() in {"up", "left"}:
            pixels = -pixels
        page.mouse.wheel(0, pixels)
        return f"Scrolled {direction}"
    except Exception as e:
        return f"FAILED: Could not scroll page: {e}"


def zoom_page(direction="in", amount=10):
    page = ensure_browser()

    try:
        change = abs(float(amount))
        if str(direction).lower() in {"out", "down", "decrease"}:
            change = -change
        zoom = page.evaluate(
            """(change) => {
                const current = parseFloat(document.body.style.zoom || '100');
                const next = Math.min(300, Math.max(25, current + change));
                document.body.style.zoom = `${next}%`;
                return next;
            }""",
            change,
        )
        return f"Zoom set to {zoom}%"
    except Exception as e:
        return f"FAILED: Could not zoom page: {e}"


# ============================================================
# TYPE INTO PLACEHOLDER
# ============================================================

def type_placeholder(placeholder, text):

    global page

    page = ensure_browser()

    try:

        # Try placeholder first
        if placeholder:

            locator = page.get_by_placeholder(
                placeholder
            ).first

            locator.fill(text)

            return f"Typed {text}"

        # Common search fields
        selectors = [
            'input[name="q"]',
            'input[type="search"]',
            'textarea',
            'input[type="text"]'
        ]

        for selector in selectors:

            try:

                locator = page.locator(
                    selector
                ).first

                if locator.is_visible():

                    locator.fill(text)

                    return f"Typed {text}"

            except Exception:
                continue

        return "FAILED: Could not find input field"

    except Exception as e:

        print("Type error:", e)

        return (
            f"FAILED: Could not type text: {e}"
        )


# ============================================================
# PRESS ENTER
# ============================================================

def press_enter():

    global page

    page = ensure_browser()

    try:

        page.keyboard.press("Enter")

        time.sleep(2)

        return "Pressed Enter"

    except Exception as e:

        print("Enter error:", e)

        return (
            f"FAILED: Could not press Enter: {e}"
        )


# ============================================================
# CLOSE BROWSER
# ============================================================

def close_browser():

    global _playwright, browser, context, page

    print("Closing browser...")

    try:

        if context:
            context.close()
        elif browser:
            browser.close()

    except Exception as e:

        print("Browser close error:", e)

    try:

        if _playwright:
            _playwright.stop()

    except Exception as e:

        print("Playwright stop error:", e)

    browser = None
    context = None
    page = None
    _playwright = None

    print("Browser closed.")

    return "Browser closed"
