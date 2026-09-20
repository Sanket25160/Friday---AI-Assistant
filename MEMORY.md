# Memory across restarts

Saved facts have no expiration. Friday writes them to `memory/facts.json`
immediately and supplies them to its chat and task planner on later runs.
Existing facts in that file are retained. Paths are relative to the project,
so launching Friday from another working directory uses the same memory.

Examples:

- "Remember that my name is Asha."
- "Remember that I live in Pune."
- "Remember that my favorite color is blue."
- "Remember that I keep my spare keys in the kitchen drawer."
- "What do you remember about me?"
- After restarting: "What is my name?"

Simple profile statements such as "My name is Asha" and "I live in Pune"
also save directly. Repeat a named profile field with a new value to update
it. Other explicit memories are saved as separate notes; repeated identical
notes are deduplicated. For arbitrary information you want retained, use
"Remember that…" rather than relying on normal chat alone.

Recent chat exchanges are saved separately in `memory/conversation.json`.
The last 20 messages are retained, and the last eight are included in model
requests to keep follow-ups useful without sending an ever-growing transcript.
Older chat messages roll out of this window; explicitly saved facts do not.
Task history continues to be stored in the project's `memory.json`.

Memory writes use a flushed temporary file and atomic replacement. Invalid
memory files raise an error instead of being silently erased. A confirmation
of a saved fact is returned only after the write succeeds.

Keep the memory files when moving or backing up the project. Saved information
is stored locally; facts and recent conversation context are sent to the
configured Groq model when generating a chat reply or task plan. Direct save
and list-memory commands do not need an AI request.

Regression checks: `python -m unittest discover -s tests -v`. The tests use
temporary memory files and mock AI, speech, and browsers; they include separate
save/restart processes launched from different folders.
