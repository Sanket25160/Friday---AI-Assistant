from tools.browser_agent import start_browser, open_website, read_page, close_browser

start_browser()

print(open_website("https://www.wikipedia.org"))

text = read_page()

print(text[:2000])

input("Press Enter to close...")

close_browser()