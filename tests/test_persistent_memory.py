"""Persistent memory checks without speech, browser access, or AI requests."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

from AI import long_memory, short_memory, memory, memory_store
from AI.classifier import classify
from AI.fast_commands import get_fast_plan
from AI.memory_commands import get_memory_plan


ROOT = Path(__file__).resolve().parents[1]


def isolated_module(name, filename, stubs):
    spec = importlib.util.spec_from_file_location(name, ROOT / "AI" / filename)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, stubs):
        spec.loader.exec_module(module)
    return module


class PersistentMemoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for module, attribute, name in (
            (long_memory, "FACTS_FILE", "facts.json"),
            (short_memory, "MEMORY_FILE", "conversation.json"),
            (memory, "MEMORY_FILE", "tasks.json"),
        ):
            patcher = patch.object(module, attribute, self.root / "memory" / name)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_facts_are_saved_immediately_and_existing_data_survives_updates(self):
        long_memory.save({"Name": "Old name", "legacy": ["existing", "data"]})
        response = long_memory.remember("name", "नमस्ते")
        saved = json.loads(long_memory.FACTS_FILE.read_text(encoding="utf-8"))
        self.assertEqual(saved, {"Name": "नमस्ते", "legacy": ["existing", "data"]})
        self.assertIn("नमस्ते", response)
        self.assertEqual(list(long_memory.FACTS_FILE.parent.glob("*.tmp")), [])

    def test_notes_do_not_overwrite_other_notes_or_duplicate_repeats(self):
        for text in ("Remember that I like tea", "Remember that I like jazz", "remember that I LIKE TEA."):
            action = get_memory_plan(text)["steps"][0]
            long_memory.remember(action["key"], action["value"])
        self.assertEqual(len(long_memory.recall()), 2)
        self.assertIn("I like jazz", long_memory.describe_memory())

    def test_updated_profile_statement_replaces_old_value(self):
        for text in ("Remember that I live in Delhi", "I live in Pune"):
            action = get_memory_plan(text)["steps"][0]
            long_memory.remember(action["key"], action["value"])
        self.assertEqual(long_memory.recall(), {"city": "Pune"})

    def test_memory_is_independent_of_current_working_directory(self):
        long_memory.remember("name", "Asha")
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            self.assertEqual(long_memory.recall(), {"name": "Asha"})
            short_memory.add_turn("Hello", "Hi")
            memory.remember("open google", [])
        finally:
            os.chdir(previous)
        self.assertEqual(short_memory.get()[0]["content"], "Hello")
        self.assertEqual(memory.load_memory()[0]["task"], "open google")

    def test_corrupt_memory_is_not_silently_overwritten(self):
        long_memory.FACTS_FILE.parent.mkdir(parents=True)
        original = '{"name": "unfinished'
        long_memory.FACTS_FILE.write_text(original, encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            long_memory.remember("city", "Pune")
        self.assertEqual(long_memory.FACTS_FILE.read_text(encoding="utf-8"), original)

    def test_interrupted_replacement_preserves_previous_memory(self):
        long_memory.remember("name", "Asha")
        with patch.object(memory_store.os, "replace", side_effect=OSError("disk unavailable")):
            with self.assertRaises(OSError):
                long_memory.remember("city", "Pune")
        self.assertEqual(long_memory.recall(), {"name": "Asha"})
        self.assertEqual(list(long_memory.FACTS_FILE.parent.glob("*.tmp")), [])

    def test_facts_outlive_recent_conversation_window(self):
        long_memory.remember("name", "Asha")
        for number in range(15):
            short_memory.add_turn(f"question {number}", f"answer {number}")
        recent = short_memory.get()
        self.assertEqual(len(recent), 20)
        self.assertEqual(recent[0]["content"], "question 5")
        self.assertEqual(recent[-1]["content"], "answer 14")
        short_memory.clear()
        self.assertEqual(short_memory.get(), [])
        self.assertEqual(long_memory.recall(), {"name": "Asha"})

    def test_saved_memory_reloads_in_a_separate_process_from_another_folder(self):
        app = self.root / "app"
        package = app / "AI"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        for filename in ("memory_store.py", "long_memory.py", "short_memory.py", "memory.py"):
            shutil.copy2(ROOT / "AI" / filename, package / filename)
        elsewhere = self.root / "different_startup_folder"
        elsewhere.mkdir()
        environment = dict(os.environ, PYTHONPATH=str(app))
        save_code = (
            "from AI.long_memory import remember; from AI.short_memory import add_turn; "
            "remember('name', 'Asha'); add_turn('Tell me about Saturn', 'Saturn is a planet')"
        )
        subprocess.run([sys.executable, "-c", save_code], cwd=app, env=environment,
                       check=True, capture_output=True, text=True, timeout=30)
        read_code = (
            "import json; from AI.long_memory import recall; from AI.short_memory import get; "
            "print(json.dumps({'facts': recall(), 'conversation': get()}))"
        )
        result = subprocess.run([sys.executable, "-c", read_code], cwd=elsewhere, env=environment,
                                check=True, capture_output=True, text=True, timeout=30)
        restored = json.loads(result.stdout)
        self.assertEqual(restored["facts"], {"name": "Asha"})
        self.assertEqual(restored["conversation"][-1]["content"], "Saturn is a planet")
        self.assertTrue((app / "memory" / "facts.json").exists())
        self.assertFalse((elsewhere / "memory").exists())

    def load_client(self):
        create = Mock(return_value=types.SimpleNamespace(choices=[
            types.SimpleNamespace(message=types.SimpleNamespace(content="Answer"))
        ]))
        groq = types.ModuleType("groq")
        groq.Groq = Mock(return_value=types.SimpleNamespace(
            chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create))
        ))
        config = types.ModuleType("config")
        config.GROQ_API_KEY = "test-only"
        module = isolated_module("memory_client_test", "client.py", {"groq": groq, "config": config})
        return module, create

    def test_chat_and_planner_requests_receive_saved_facts_and_previous_turns(self):
        long_memory.remember("name", "Asha")
        short_memory.add_turn("Tell me about Saturn", "Saturn is a planet")
        client, create = self.load_client()
        for method in (client.ask_chat, client.ask_agent):
            with self.subTest(method=method.__name__), patch("builtins.print"):
                self.assertEqual(method("What about its moons?", "System instructions"), "Answer")
                messages = create.call_args.kwargs["messages"]
                self.assertEqual(messages[0]["content"], "System instructions")
                self.assertIn('"name": "Asha"', messages[1]["content"])
                self.assertEqual(messages[-3:], [
                    {"role": "user", "content": "Tell me about Saturn"},
                    {"role": "assistant", "content": "Saturn is a planet"},
                    {"role": "user", "content": "What about its moons?"},
                ])
        self.assertEqual(len(short_memory.get()), 2)  # Internal planning isn't conversation.

    def test_chat_saves_complete_turn_before_returning_with_one_model_call(self):
        client = types.ModuleType("AI.client")
        client.ask_chat = Mock(return_value="Saturn has many moons.")
        chat = isolated_module("memory_chat_test", "chat.py", {"AI.client": client})
        self.assertEqual(chat.chat("What about its moons?"), "Saturn has many moons.")
        client.ask_chat.assert_called_once()
        self.assertEqual(short_memory.get(), [
            {"role": "user", "content": "What about its moons?"},
            {"role": "assistant", "content": "Saturn has many moons."},
        ])

    def test_failed_chat_request_does_not_save_a_fictitious_answer(self):
        client = types.ModuleType("AI.client")
        client.ask_chat = Mock(side_effect=RuntimeError("offline"))
        chat = isolated_module("memory_chat_failure_test", "chat.py", {"AI.client": client})
        with self.assertRaises(RuntimeError):
            chat.chat("Hello")
        self.assertEqual(short_memory.get(), [])


class MemoryCommandTests(unittest.TestCase):
    def test_explicit_and_simple_profile_statements_use_existing_executor_path(self):
        for text in ("Remember that my name is Asha.", "My name is Asha", "Please remember my name is Asha"):
            with self.subTest(text=text):
                self.assertEqual(classify(text), "command")
                self.assertEqual(get_fast_plan(text), {"steps": [
                    {"tool": "remember_fact", "key": "name", "value": "Asha"},
                    {"tool": "finish"},
                ]})

    def test_recall_commands_do_not_call_the_model(self):
        for text in ("What do you remember about me?", "Show my memories", "list my memories"):
            with self.subTest(text=text):
                self.assertEqual(classify(text), "command")
                self.assertEqual(get_fast_plan(text)["steps"][0], {"tool": "recall_memory"})

    def test_questions_empty_and_compound_requests_are_not_saved_as_facts(self):
        for text in (
            "Remember", "Remember that", "remember this:", "keep in mind that",
            "My name is Asha?", "Remember my name?", "What is my name?",
            "Don't remember my name", "Remember that my name is Asha and open google",
            "Remember that I like tea. Open youtube", "Remember that I like tea, search google for cups",
            "Remember that I like tea if I say yes", "My name is not Asha",
        ):
            with self.subTest(text=text):
                self.assertIsNone(get_memory_plan(text))


if __name__ == "__main__":
    unittest.main()
