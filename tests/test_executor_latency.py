"""Verify quiet intermediate statuses never hide requested spoken content."""

import importlib.util
from pathlib import Path
import sys
import types
import tempfile
import unittest
from unittest.mock import Mock, call, patch
from AI import long_memory
from AI.fast_commands import get_fast_plan


def load_executor():
    dependencies = {
        "speech.speaker": ["speak_sync"],
        "tools.browser_agent": [
            "open_website", "search_google", "search_youtube", "read_page", "get_links",
            "click_text", "scroll_page", "zoom_page", "type_placeholder",
            "press_enter", "close_browser",
        ],
        "tools.files": ["create_file", "write_file", "read_file"],
        "tools.music": ["play_song"],
        "tools.news": ["get_news"],
    }
    modules = {}
    for name, functions in dependencies.items():
        module = types.ModuleType(name)
        for function in functions:
            setattr(module, function, Mock())
        modules[name] = module
    path = Path(__file__).resolve().parents[1] / "AI" / "executor.py"
    spec = importlib.util.spec_from_file_location("executor_under_test", path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


class ExecutorLatencyTests(unittest.TestCase):
    def setUp(self):
        self.executor = load_executor()

    def execute(self, action, **kwargs):
        with patch("builtins.print"):
            return self.executor.execute(action, **kwargs)

    def test_intermediate_status_is_silent_but_result_is_preserved(self):
        self.executor.search_google.return_value = "Searched Google for cats"
        result = self.execute({"tool": "search_google", "query": "cats"}, announce=False)
        self.assertEqual(result, "Searched Google for cats")
        self.executor.search_google.assert_called_once_with("cats")
        self.executor.speak_sync.assert_not_called()

    def test_default_final_status_is_spoken(self):
        self.executor.search_google.return_value = "Searched Google for cats"
        self.execute({"tool": "search_google", "query": "cats"})
        self.executor.speak_sync.assert_called_once_with("Searched Google for cats")

    def test_chat_is_spoken_even_with_announcements_disabled(self):
        self.execute({"tool": "chat", "response": "Here is your answer."}, announce=False)
        self.executor.speak_sync.assert_called_once_with("Here is your answer.")

    def test_requested_file_contents_are_spoken_even_when_intermediate(self):
        self.executor.read_file.return_value = "Contents of the file"
        result = self.execute({"tool": "read_file", "filename": "notes.txt"}, announce=False)
        self.assertEqual(result, "Contents of the file")
        self.executor.speak_sync.assert_called_once_with("Contents of the file")

    def test_failures_are_spoken_even_when_intermediate(self):
        self.executor.click_text.return_value = "FAILED: element not found"
        result = self.execute({"tool": "click_text", "text": "Missing"}, announce=False)
        self.assertEqual(result, "FAILED: element not found")
        self.executor.speak_sync.assert_called_once_with("FAILED: element not found")

    def test_scroll_and_zoom_route_optional_arguments(self):
        self.execute({"tool": "scroll_page", "direction": "up", "amount": 800})
        self.executor.scroll_page.assert_called_once_with("up", 800)
        self.executor.speak_sync.reset_mock()

        self.execute({"tool": "zoom_page", "direction": "out", "amount": 15})
        self.executor.zoom_page.assert_called_once_with("out", 15)

    def test_raw_page_text_is_not_spoken(self):
        self.executor.read_page.return_value = "Full article to summarize"
        result = self.execute({"tool": "read_page"})
        self.assertEqual(result, "Full article to summarize")
        self.executor.speak_sync.assert_not_called()

    def test_news_still_reads_requested_headlines(self):
        self.executor.get_news.return_value = [{"title": "First story"}, {"title": "Second story"}]
        self.execute({"tool": "speak_news"}, announce=False)
        self.assertEqual(self.executor.speak_sync.call_args_list, [
            call("First story"), call("Second story"),
        ])

    def test_unknown_tool_failure_remains_spoken(self):
        result = self.execute({"tool": "unknown"}, announce=False)
        self.assertEqual(result, "FAILED: Unknown tool")
        self.executor.speak_sync.assert_called_once_with("I don't know how to do that yet.")

    def test_memory_plan_saves_before_speaking_and_can_be_read_back(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "facts.json"
            with patch.object(long_memory, "FACTS_FILE", path):
                def check_saved_before_speaking(text):
                    self.assertEqual(long_memory.recall(), {"name": "Asha"})
                self.executor.speak_sync.side_effect = check_saved_before_speaking
                action = get_fast_plan("Remember that my name is Asha")["steps"][0]
                result = self.execute(action)
                self.assertIn("Asha", result)
                self.assertTrue(path.exists())
                self.executor.speak_sync.reset_mock()
                recalled = self.execute({"tool": "recall_memory"}, announce=False)
                self.assertIn("name: Asha", recalled)
                self.executor.speak_sync.assert_called_once_with(recalled)

    def test_memory_write_failure_never_announces_success(self):
        with patch.object(self.executor, "remember_fact", side_effect=OSError("disk unavailable")):
            with patch("traceback.print_exc"):
                result = self.execute({"tool": "remember_fact", "key": "name", "value": "Asha"})
        self.assertTrue(result.startswith("FAILED:"))
        self.executor.speak_sync.assert_not_called()


if __name__ == "__main__":
    unittest.main()
