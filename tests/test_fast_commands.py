import unittest

from AI.fast_commands import get_fast_plan


class FastCommandTests(unittest.TestCase):
    def test_known_websites_produce_complete_plans(self):
        websites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "chatgpt": "https://www.chatgpt.com",
            "github": "https://www.github.com",
            "linkedin": "https://www.linkedin.com",
            "instagram": "https://www.instagram.com",
            "whatsapp": "https://web.whatsapp.com",
            "whatsapp web": "https://web.whatsapp.com",
            "bbc": "https://www.bbc.com",
        }
        for site, url in websites.items():
            with self.subTest(site=site):
                self.assertEqual(get_fast_plan("open " + site), {
                    "steps": [
                        {"tool": "open_website", "website": url},
                        {"tool": "finish"},
                    ]
                })

    def test_politeness_case_and_speech_punctuation(self):
        expected = get_fast_plan("open youtube")
        for command in (
            "  PLEASE open YouTube!  ",
            "Open YouTube please.",
            "Please   open   YouTube, please?",
            "Please, open YouTube.",
        ):
            with self.subTest(command=command):
                self.assertEqual(get_fast_plan(command), expected)

    def test_close_browser(self):
        for command in ("close browser", "Please close the browser."):
            with self.subTest(command=command):
                self.assertEqual(get_fast_plan(command), {
                    "steps": [{"tool": "close_browser"}, {"tool": "finish"}]
                })

    def test_explicit_search_keeps_query_case(self):
        for engine in ("Google", "YouTube"):
            with self.subTest(engine=engine):
                self.assertEqual(
                    get_fast_plan("Please search " + engine + " for Python C++ please."),
                    {"steps": [
                        {"tool": "search_" + engine.lower(), "query": "Python C++"},
                        {"tool": "finish"},
                    ]},
                )

    def test_compound_commands_are_left_to_planner(self):
        commands = (
            "open google and then search for cats",
            "open youtube then play music",
            "open github and read the page",
            "close the browser and open google",
            "search google for Python then open the first result",
            "search youtube for jazz and play the first video",
            "search google for cats, read the first result",
            "search google for cats; close the browser",
            "search google for cats. Tell me the result",
            "search google for cats\nopen youtube",
            "search google for Python also summarize it",
            "search google for cats please tell me the results",
            "search google for Python tutorials but only return the first result",
            "search google for flights sort by cheapest",
            "search youtube for jazz plus launch Spotify",
            "search google for cats with pictures",
            "search google for Python tutorials without opening a browser",
            "search youtube for jazz while downloading the song",
            "search google for cats when the browser is ready",
            "search google for cats if the internet is available",
            "search google for flights unless the prices are outdated",
            "search google for flights until a cheap fare appears",
            "search google for cats once the browser is ready",
            "search google for cats filter the results",
            "search google for flights compare the fares",
            "search google for cats select the first result",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNone(get_fast_plan(command))

    def test_unknown_quoted_and_unrelated_requests_use_planner(self):
        commands = (
            None, 42, "", "please", "open", "open notepad", "open example.com",
            "open google maps", "I said open google", '"open google"',
            "don't open google", "can you open google", "close browser tabs",
            "search google for", "search google for  ", "search for Python",
            "search google for ---", "search google for +++",
            'search google for "Python"', "search google for rock and roll",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNone(get_fast_plan(command))

    def test_each_plan_is_independent(self):
        first = get_fast_plan("open google")
        first["steps"][0]["website"] = "changed"
        first["steps"].pop()
        second = get_fast_plan("open google")
        self.assertEqual(second["steps"][0]["website"], "https://www.google.com")
        self.assertEqual(second["steps"][-1], {"tool": "finish"})


if __name__ == "__main__":
    unittest.main()
