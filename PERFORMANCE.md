# Command response time

Friday now sends exact commands such as `open youtube`, `close the browser`,
and `search google for Python tutorials` straight to the existing tools.
These commands skip the AI planner. Unknown or compound requests still use
the planner, and failed direct commands return to it for recovery.

Other changes reduce work on the command path:

- Removed the one-second pause after each agent action and the two-second
  pauses after Google and YouTube searches. Browser navigation still waits
  for DOM content to load; click and Enter waits are unchanged.
- Intermediate status announcements no longer hold up a batch of actions.
  Final status, chat answers, file contents, and tool failure messages keep
  their existing speech behavior.
- The planner reads full browser text when planning; action history uses
  page metadata instead of repeatedly extracting the body.
- Whisper receives audio in memory without a temporary WAV file. Its model,
  language detection, and decoding settings are unchanged.
- Startup no longer launches the unused microphone monitor's CPU spin loop.
  Command listening and speech interruption keep their own audio listeners.

The console reports `Whisper:` for the complete transcription, including
segment decoding. `[Latency] Planning`, `[Latency] Tool`, and
`[Latency] Task execution` show the other stages. Tool timing excludes spoken
feedback; task execution includes it and memory saving, but excludes optional
follow-up suggestions. Compare the same commands after startup to measure
the improvement on your machine. AI, network, page load, and TTS time still vary.

Run the isolated regression checks with a working Python environment containing
NumPy:

```powershell
python -m unittest discover -s tests -v
```

These checks mock microphones, AI services, speech, and browser automation;
they do not measure live recognition accuracy or network latency.
