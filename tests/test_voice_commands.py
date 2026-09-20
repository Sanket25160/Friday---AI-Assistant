import unittest

from speech.commands import is_sleep_command
from speech.language import detect_language
from speech.wakeword import contains_wakeword, is_clap_or_snap


class VoiceCommandTests(unittest.TestCase):
    def test_detects_hindi_for_devanagari_text(self):
        self.assertEqual(detect_language("नमस्ते, आप कैसे हैं?"), "hi")
        self.assertEqual(detect_language("Hello, how are you?"), "en")

    def test_supported_wake_phrases(self):
        for command in ("Friday", "Hey Friday", "Wake up", "Come on, get up"):
            with self.subTest(command=command):
                self.assertTrue(contains_wakeword(command))
        self.assertFalse(contains_wakeword("Hey assistant"))

    def test_clap_or_snap_requires_a_sharp_loud_transient(self):
        self.assertTrue(is_clap_or_snap([0.0] * 64 + [0.8] + [0.0] * 64))
        self.assertFalse(is_clap_or_snap([0.1, 0.1, 0.1], threshold=0.25))
        self.assertFalse(is_clap_or_snap([0.7] * 16))

    def test_sleep_phrases_ignore_case_and_punctuation(self):
        commands = (
            "go to sleep", "GO TO SLEEP!", "go back to sleep", "sleep",
            "take a rest.", "Take, a rest", "I will see you later",
            "see you later", "you can go", "bye bye", "bye",
            "I am going", "I am going now", "please go to sleep",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(is_sleep_command(command))

    def test_sleep_detector_rejects_embedded_phrases(self):
        for command in (
            "please go to sleep and wake me later",
            "please sleep on this page",
            "take a break",
            "goodbye everyone",
        ):
            with self.subTest(command=command):
                self.assertFalse(is_sleep_command(command))


if __name__ == "__main__":
    unittest.main()