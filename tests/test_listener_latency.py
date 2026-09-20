"""Listener regression checks without microphone access or speech models."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np


def fake_module(name, **attributes):
    module = ModuleType(name)
    module.__dict__.update(attributes)
    return module


class FakeInputStream:
    def __init__(self):
        self.closed = False
        self.read_count = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.closed = True

    def read(self, blocksize):
        self.read_count += 1
        # Use noncontiguous input to verify the decoder always gets contiguous
        # mono audio even when the input backend supplies a strided view.
        audio = np.full((blocksize, 2), 0.25, dtype=np.float32)[:, :1]
        return audio, False


class ListenerLatencyTests(unittest.TestCase):
    def setUp(self):
        stubs = {
            "silero_vad": fake_module(
                "silero_vad", load_silero_vad=Mock(), VADIterator=Mock()
            ),
            "faster_whisper": fake_module("faster_whisper", WhisperModel=Mock()),
            "sounddevice": fake_module("sounddevice", InputStream=Mock()),
            "torch": fake_module("torch", from_numpy=lambda array: array),
            "speech.state": fake_module("speech.state", interrupt_event=Mock()),
        }
        path = Path(__file__).resolve().parents[1] / "speech" / "listener.py"
        spec = importlib.util.spec_from_file_location("listener_latency_test", path)
        self.listener = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, stubs):
            spec.loader.exec_module(self.listener)

    def capture(self, events, transcribe):
        stream = FakeInputStream()
        vad = Mock(side_effect=events)
        model = SimpleNamespace(transcribe=transcribe)
        self.listener.get_model = Mock(return_value=model)
        self.listener.get_vad = Mock(return_value=vad)
        self.listener.sd.InputStream.return_value = stream
        return stream, vad

    def test_transcribes_memory_after_releasing_microphone_and_times_lazy_decode(self):
        clock = [10.0]

        def transcribe(audio, **options):
            self.assertTrue(stream.closed)
            self.assertIsInstance(audio, np.ndarray)
            self.assertEqual(audio.ndim, 1)
            self.assertEqual(audio.dtype, np.float32)
            self.assertTrue(audio.flags.c_contiguous)
            self.assertTrue(np.all(audio == 0.25))
            self.assertEqual(options, {})  # Preserve language/decoder defaults.
            clock[0] += 0.75

            def segments():
                clock[0] += 3.25
                yield SimpleNamespace(text="  namaste")
                yield SimpleNamespace(text=" duniya  ")

            return segments(), SimpleNamespace(language="hi")

        stream, vad = self.capture(
            [{"start": 0}] + [None] * 38 + [{"end": 20480}], transcribe
        )
        with (
            patch("builtins.open", side_effect=AssertionError("No audio file I/O")),
            patch("builtins.print") as output,
            patch.object(self.listener.time, "perf_counter", side_effect=lambda: clock[0]),
        ):
            result = self.listener.listen()

        self.assertEqual(result, {"text": "namaste duniya", "language": "hi"})
        self.assertEqual(stream.read_count, 40)
        vad.reset_states.assert_called_once_with()
        output.assert_any_call("Whisper:", 4.0)
        self.listener.sd.InputStream.assert_called_once_with(
            samplerate=16000, channels=1, dtype="float32", blocksize=512
        )

    def test_short_recordings_still_skip_transcription(self):
        transcribe = Mock()
        stream, _ = self.capture([{"start": 0}, {"end": 1024}], transcribe)
        with patch("builtins.print"):
            result = self.listener.listen()
        self.assertEqual(result, "")
        self.assertTrue(stream.closed)
        transcribe.assert_not_called()

    def test_empty_recordings_still_skip_transcription(self):
        transcribe = Mock()
        stream, _ = self.capture([{"end": 512}], transcribe)
        with patch("builtins.print"):
            result = self.listener.listen()
        self.assertEqual(result, "")
        self.assertTrue(stream.closed)
        transcribe.assert_not_called()

    def test_microphone_is_released_when_decoder_raises(self):
        transcribe = Mock(side_effect=RuntimeError("decode failed"))
        stream, _ = self.capture(
            [{"start": 0}] + [None] * 38 + [{"end": 20480}], transcribe
        )
        with patch("builtins.print"), self.assertRaisesRegex(RuntimeError, "decode failed"):
            self.listener.listen()
        self.assertTrue(stream.closed)


if __name__ == "__main__":
    unittest.main()
