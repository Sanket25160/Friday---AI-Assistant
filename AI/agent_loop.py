from AI.agent import decide
from AI.client import answer_from_browser
from AI.executor import execute
from AI.memory import remember
from tools.browser_agent import browser_state
from speech.interrupt import interrupt_event
from AI.followup import handle_followup_permission
from AI.fast_commands import get_fast_plan
import time

def run_agent(task, allow_followup=True):

    started = time.perf_counter()

    goal = {
        "task": task
    }

    history = []
    retries = {}
    max_iterations = 10
    iteration = 0
    state = {"title": "", "url": "", "text": ""}
    pending_plan = get_fast_plan(task)

    def complete_task(offer_followup=False):
        remember(task, history)
        print(f"[Latency] Task execution: {time.perf_counter() - started:.2f}s")
        memory_only = history and all(
            item["action"].get("tool") in {"remember_fact", "recall_memory"}
            for item in history
        )
        if allow_followup and offer_followup and history and not memory_only:
            handle_followup_permission(task, state, history, run_agent)

    while iteration < max_iterations:
        iteration += 1

        if interrupt_event.is_set():
            print("Interrupted by user. Halting current agent task.")
            interrupt_event.clear()
            complete_task()
            return

        if pending_plan is not None:
            print("[Latency] Using direct command route (no planner request).")
            plan = pending_plan
            pending_plan = None
        else:
            state = browser_state()
            planning_started = time.perf_counter()
            plan = decide(task, state, history, goal)
            print(f"[Latency] Planning: {time.perf_counter() - planning_started:.2f}s")

        print(plan)

        if not plan or not plan.get("steps"):
            complete_task(offer_followup=True)
            return

        for index, action in enumerate(plan["steps"]):

            if interrupt_event.is_set():
                print("Interrupted by user. Halting current agent task.")
                interrupt_event.clear()
                complete_task()
                return

            # If fallback error chat is returned, execute speech and exit loop
            if action.get("tool") == "chat" and action.get("response", "").startswith("Sorry boss, I didn't understand"):
                execute(action)
                complete_task()
                return

            action_key = str(action)

            if action_key not in retries:
                retries[action_key] = 0

            # Keep spoken answers/errors, but do not make the next action wait
            # for a status announcement when more work is already planned.
            announce = not any(
                step.get("tool") != "finish"
                for step in plan["steps"][index + 1:]
            )
            result = execute(action, announce=announce)

            if interrupt_event.is_set():
                print("Interrupted by user during tool execution. Halting task.")
                interrupt_event.clear()
                complete_task()
                return

            if isinstance(result, str) and result.startswith("FAILED"):

                history.append({
                    "action": action,
                    "result": result,
                    "url": state.get("url", ""),
                    "title": state.get("title", ""),
                    "timestamp": time.time()
                })

                retries[action_key] += 1

                if retries[action_key] >= 3:
                    print(f"{action_key} failed 3 times.")
                    complete_task()
                    return

                print("Tool failed. Asking the agent to replan...")
                break

            if result == "DONE":
                print("Agent finished.")
                complete_task(offer_followup=True)
                return

            # History and follow-up suggestions only need page metadata. Read
            # the full page once when the planner actually needs another turn.
            if action["tool"] not in {"remember_fact", "recall_memory"}:
                state = browser_state(include_text=False)

            if action["tool"] == "read_page":

                page_text = result

                summary = answer_from_browser(
                    task,
                    page_text
                )

                chat_action = {
                    "tool": "chat",
                    "response": summary
                }

                execute(chat_action)

                history.append({
                    "action": chat_action,
                    "result": summary,
                    "url": state.get("url", ""),
                    "title": state.get("title", ""),
                    "timestamp": time.time()
                })

                continue

            if result != "FAILED":

                history.append({
                    "action": action,
                    "result": result,
                    "url": state.get("url", ""),
                    "title": state.get("title", ""),
                    "timestamp": time.time()
                })

    complete_task(offer_followup=True)
