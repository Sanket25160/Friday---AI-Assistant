from playwright.sync_api import sync_playwright
from urllib.parse import quote

playwright = None
browser = None
page = None


def start_browser():
    global playwright, browser, page

    if browser is None:
        playwright = sync_playwright().start()

        browser = playwright.chromium.launch(
            headless=False,
            args=["--start-maximized"]
        )

        page = browser.new_page(no_viewport=True)

    return page

def search_google(query):

    page = start_browser()

    page.goto(
        "https://www.google.com/search?q=" + quote(query)
    )

def search_youtube(query):

    page = start_browser()

    page.goto(
        "https://www.youtube.com/results?search_query="
        + quote(query)
    )

def open_website(url):

    page = start_browser()

    if not url.startswith("http"):
        url = "https://" + url

    page.goto(
    url,
    wait_until="networkidle"
)

def read_page():

    page = start_browser()

    return page.locator("body").inner_text()

def get_links():

    page = start_browser()

    links = page.locator("a").all()

    return [link.inner_text() for link in links]

def click_text(text):

    page = start_browser()

    page.get_by_text(text).click()

def type_placeholder(placeholder, text):

    page = start_browser()

    page.get_by_placeholder(placeholder).fill(text)

def press_enter():

    page = start_browser()

    page.keyboard.press("Enter")

def close_browser():
    global playwright, browser, page

    if browser:
        browser.close()

    if playwright:
        playwright.stop()

    browser = None
    page = None
    playwright = None

def browser_state():

    page = start_browser()

    return {
        "title": page.title(),
        "url": page.url,
        "text": page.locator("body").inner_text()[:4000]
    }