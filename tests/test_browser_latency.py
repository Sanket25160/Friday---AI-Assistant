"""Browser timing regressions without launching a browser or using the network."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


def load_browser_agent():
    # Import an isolated copy so tests neither require Playwright nor replace the
    # live tools.browser_agent module used by other tests or the application.
    playwright = types.ModuleType("playwright")
    sync_api = types.ModuleType("playwright.sync_api")
    sync_api.sync_playwright = Mock()
    sync_api.TimeoutError = TimeoutError
    playwright.sync_api = sync_api
    path = Path(__file__).resolve().parents[1] / "tools" / "browser_agent.py"
    spec = importlib.util.spec_from_file_location("browser_agent_under_test", path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"playwright": playwright, "playwright.sync_api": sync_api}):
        # The production module configures console encoding at import time.
        with patch.object(sys, "stdout", Mock()), patch.object(sys, "stderr", Mock()):
            spec.loader.exec_module(module)
    return module


class BrowserLatencyTests(unittest.TestCase):
    def setUp(self):
        self.agent = load_browser_agent()
        self.page = Mock()
        self.page.url = "https://example.com/"
        self.page.title.return_value = "Example"
        self.page.locator.return_value.inner_text.return_value = "Full page contents"

    def test_searches_wait_for_dom_without_fixed_sleep(self):
        searches = (
            ("search_google", "https://www.google.com/search?q=machine+learning", "Google"),
            ("search_youtube", "https://www.youtube.com/results?search_query=machine+learning", "YouTube"),
        )
        for name, url, service in searches:
            with self.subTest(search=name):
                self.page.reset_mock()
                with patch.object(self.agent, "ensure_browser", return_value=self.page):
                    with patch.object(self.agent.time, "sleep") as sleep:
                        result = getattr(self.agent, name)(" machine learning ")
                self.page.goto.assert_called_once_with(
                    url, wait_until="domcontentloaded", timeout=30000
                )
                sleep.assert_not_called()
                self.assertEqual(result, f"Searched {service} for machine learning")

    def test_navigation_failures_still_return_failure(self):
        for name in ("open_website", "search_google", "search_youtube"):
            with self.subTest(action=name):
                self.page.goto.side_effect = TimeoutError("navigation timed out")
                with patch.object(self.agent, "ensure_browser", return_value=self.page):
                    result = getattr(self.agent, name)("example.com")
                self.assertTrue(result.startswith("FAILED:"))
                self.assertIn("navigation timed out", result)

    def test_search_query_symbols_are_encoded(self):
        for name in ("search_google", "search_youtube"):
            with self.subTest(action=name):
                with patch.object(self.agent, "ensure_browser", return_value=self.page):
                    getattr(self.agent, name)("C++ C#")
                self.assertTrue(self.page.goto.call_args.args[0].endswith("=C%2B%2B+C%23"))

    def test_scroll_and_zoom_use_current_page(self):
        with patch.object(self.agent, "ensure_browser", return_value=self.page):
            self.assertEqual(self.agent.scroll_page("up", 800), "Scrolled up")
            self.page.mouse.wheel.assert_called_once_with(0, -800.0)

            self.page.evaluate.return_value = 85.0
            self.assertEqual(self.agent.zoom_page("out", 15), "Zoom set to 85.0%")
            self.page.evaluate.assert_called_once()

    def test_empty_state_does_not_launch_browser(self):
        for include_text in (True, False):
            with self.subTest(include_text=include_text):
                with patch.object(self.agent, "start_browser") as start:
                    state = self.agent.browser_state(include_text=include_text)
                start.assert_not_called()
                self.assertEqual(state, {"title": "", "url": "", "text": ""})

    def test_metadata_only_state_does_not_read_body(self):
        self.agent.page = self.page
        state = self.agent.browser_state(include_text=False)
        self.assertEqual(state, {"title": "Example", "url": self.page.url, "text": ""})
        self.page.title.assert_called_once_with()
        self.page.locator.assert_not_called()

    def test_default_state_preserves_full_page_text(self):
        self.agent.page = self.page
        full_text = "page contents " * 1000
        self.page.locator.return_value.inner_text.return_value = full_text
        state = self.agent.browser_state()
        self.assertEqual(state, {"title": "Example", "url": self.page.url, "text": full_text})
        self.page.title.assert_called_once_with()
        self.page.locator.assert_called_once_with("body")
        self.page.locator.return_value.inner_text.assert_called_once_with()

    def test_closed_page_returns_empty_state(self):
        self.agent.page = self.page
        self.page.title.side_effect = RuntimeError("page closed")
        self.assertEqual(self.agent.browser_state(), {"title": "", "url": "", "text": ""})
        self.page.locator.assert_not_called()


if __name__ == "__main__":
    unittest.main()
