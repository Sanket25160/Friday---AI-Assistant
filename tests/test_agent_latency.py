"""Agent control-flow tests with real direct routing and no external services."""

import importlib.util
from pathlib import Path
import sys
import threading
import types
import unittest
from unittest.mock import Mock, call, patch


def stub_module(name, **attributes):
    module = types.ModuleType(name)
    module.__dict__.update(attributes)
    return module


def load_agent_loop():
    interrupt = threading.Event()
    modules = {
        "AI.agent": stub_module("AI.agent", decide=Mock()),
        "AI.client": stub_module("AI.client", answer_from_browser=Mock()),
        "AI.executor": stub_module("AI.executor", execute=Mock()),
        "AI.memory": stub_module("AI.memory", remember=Mock()),
        "AI.followup": stub_module("AI.followup", handle_followup_permission=Mock()),
        "tools.browser_agent": stub_module("tools.browser_agent", browser_state=Mock()),
        "speech.interrupt": stub_module("speech.interrupt", interrupt_event=interrupt),
    }
    path = Path(__file__).resolve().parents[1] / "AI" / "agent_loop.py"
    spec = importlib.util.spec_from_file_location("agent_loop_under_test", path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


class AgentLatencyTests(unittest.TestCase):
    def setUp(self):
        self.agent = load_agent_loop()
        self.agent.execute.side_effect = (
            lambda action, announce=True: "DONE" if action["tool"] == "finish" else "Success"
        )
        self.agent.browser_state.side_effect = lambda include_text=True: {
            "title": "Example", "url": "https://example.com/",
            "text": "Full page text" if include_text else "",
        }
        self.finish = {"tool": "finish"}

    def run_task(self, task="perform a complex browser task"):
        with patch("builtins.print"):
            self.agent.run_agent(task, allow_followup=False)

    def test_fast_plan_skips_planner_and_full_page_snapshot(self):
        self.run_task("open google")
        self.agent.decide.assert_not_called()
        self.assertEqual(self.agent.execute.call_args_list, [
            call({"tool": "open_website", "website": "https://www.google.com"}, announce=True),
            call(self.finish, announce=True),
        ])
        self.agent.browser_state.assert_called_once_with(include_text=False)
        self.agent.remember.assert_called_once()
        self.agent.handle_followup_permission.assert_not_called()

    def test_memory_command_needs_no_planner_browser_or_proactive_followup(self):
        with patch("builtins.print"):
            self.agent.run_agent("Remember that my name is Asha", allow_followup=True)
        self.agent.decide.assert_not_called()
        self.agent.browser_state.assert_not_called()
        self.agent.handle_followup_permission.assert_not_called()
        self.assertEqual(self.agent.execute.call_args_list, [
            call({"tool": "remember_fact", "key": "name", "value": "Asha"}, announce=True),
            call(self.finish, announce=True),
        ])

    def test_failed_fast_action_falls_back_to_planner(self):
        recovery = {"tool": "chat", "response": "The website is unavailable."}
        self.agent.execute.side_effect = ["FAILED: site unavailable", "Spoken", "DONE"]
        self.agent.decide.return_value = {"steps": [recovery, self.finish]}
        self.run_task("open google")
        self.agent.decide.assert_called_once()
        self.assertEqual(self.agent.execute.call_args_list[1:], [
            call(recovery, announce=True), call(self.finish, announce=True),
        ])
        self.assertEqual(self.agent.browser_state.call_args_list, [
            call(), call(include_text=False),
        ])
        history = self.agent.remember.call_args.args[1]
        self.assertEqual(history[0]["result"], "FAILED: site unavailable")

    def test_multistep_plan_speaks_last_status_and_has_no_fixed_sleep(self):
        first = {"tool": "type_placeholder", "placeholder": "Search", "text": "cats"}
        second = {"tool": "press_enter"}
        self.agent.decide.return_value = {"steps": [first, second, self.finish]}
        with patch.object(self.agent.time, "sleep") as sleep:
            self.run_task()
        self.assertEqual(self.agent.execute.call_args_list, [
            call(first, announce=False), call(second, announce=True),
            call(self.finish, announce=True),
        ])
        sleep.assert_not_called()
        self.assertEqual(self.agent.browser_state.call_args_list, [
            call(), call(include_text=False), call(include_text=False),
        ])

    def test_failure_stops_batch_and_identical_retries_are_capped(self):
        failing = {"tool": "click_text", "text": "Missing button"}
        remaining = {"tool": "press_enter"}
        self.agent.decide.return_value = {"steps": [failing, remaining, self.finish]}
        self.agent.execute.return_value = "FAILED: element not found"
        self.agent.execute.side_effect = None
        self.run_task()
        self.assertEqual(self.agent.execute.call_args_list, [call(failing, announce=False)] * 3)
        self.assertEqual(self.agent.decide.call_count, 3)
        self.assertEqual(self.agent.browser_state.call_args_list, [call()] * 3)
        history = self.agent.remember.call_args.args[1]
        self.assertEqual(len(history), 3)
        self.assertTrue(all(item["result"].startswith("FAILED") for item in history))

    def test_interrupt_during_tool_prevents_remaining_steps(self):
        first = {"tool": "click_text", "text": "Continue"}
        self.agent.decide.return_value = {"steps": [first, {"tool": "press_enter"}, self.finish]}

        def interrupted_execution(action, announce=True):
            self.agent.interrupt_event.set()
            return "Success"

        self.agent.execute.side_effect = interrupted_execution
        self.run_task()
        self.agent.execute.assert_called_once_with(first, announce=False)
        self.assertFalse(self.agent.interrupt_event.is_set())
        self.agent.remember.assert_called_once()

    def test_existing_interrupt_prevents_direct_action(self):
        self.agent.interrupt_event.set()
        self.run_task("open google")
        self.agent.execute.assert_not_called()
        self.agent.decide.assert_not_called()
        self.agent.browser_state.assert_not_called()
        self.assertFalse(self.agent.interrupt_event.is_set())

    def test_new_planning_turn_receives_full_state_after_metadata_update(self):
        search = {"tool": "search_google", "query": "cats"}
        answer = {"tool": "chat", "response": "The search is complete."}
        self.agent.decide.side_effect = [
            {"steps": [search]}, {"steps": [answer, self.finish]},
        ]
        self.run_task()
        self.assertEqual(self.agent.browser_state.call_args_list, [
            call(), call(include_text=False), call(), call(include_text=False),
        ])
        for planner_call in self.agent.decide.call_args_list:
            self.assertEqual(planner_call.args[1]["text"], "Full page text")

    def test_read_page_answer_is_still_spoken(self):
        read = {"tool": "read_page"}
        self.agent.decide.return_value = {"steps": [read, self.finish]}
        self.agent.execute.side_effect = ["Page article", "Page summary", "DONE"]
        self.agent.answer_from_browser.return_value = "Page summary"
        self.run_task()
        self.agent.answer_from_browser.assert_called_once_with(
            "perform a complex browser task", "Page article"
        )
        self.assertEqual(self.agent.execute.call_args_list[1],
                         call({"tool": "chat", "response": "Page summary"}))


if __name__ == "__main__":
    unittest.main()
