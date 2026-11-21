"""Prints one sample from a finished run: its scores, final code and conversation.

Run from the repo root (the run is the folder name in logs/, the task can be "132" or "HumanEval/132"):

    python analysis/show_sample.py deepseek_humanevalplus_agent 132 1     # task 132, epoch 1
    python analysis/show_sample.py deepseek_humanevalplus_single 99       # every epoch of task 99
"""

import sys
from pathlib import Path

from inspect_ai.log import read_eval_log

LOG_ROOT = Path(__file__).resolve().parents[1] / "logs"


def main() -> None:
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    run, task = sys.argv[1], sys.argv[2]
    task = task if "/" in task else f"HumanEval/{task}"
    epoch = int(sys.argv[3]) if len(sys.argv) == 4 else None

    log_path = sorted((LOG_ROOT / run).glob("*.eval"))[-1]
    samples = [
        s for s in read_eval_log(str(log_path)).samples
        if s.id == task and (epoch is None or s.epoch == epoch)
    ]
    if not samples:
        sys.exit(f"No sample {task} (epoch {epoch or 'any'}) in {log_path.name}")

    for sample in samples:
        print(f"\n{'=' * 30} {task}, epoch {sample.epoch} {'=' * 30}")
        for name, score in (sample.scores or {}).items():
            meta = score.metadata or {}
            keys = ["end_reason", "test_modified", "visible_original_pass", "extra_files",
                    "hidden_status", "hidden_error"]
            print(f"{name}: {score.value}  " + "  ".join(f"{k}={meta[k]}" for k in keys if k in meta))

        print("\n--- final code (func.py) ---")
        print(sample.scores["visible_tests"].answer)

        print("--- conversation ---")
        for message in sample.messages:
            if message.role == "system":
                continue
            text = (message.text or "").strip()
            if text:
                print(f"[{message.role}] {text[:1500]}")
            for call in getattr(message, "tool_calls", None) or []:
                args = call.arguments.get("command") or call.arguments.get("code") or call.arguments
                print(f"[{message.role} -> {call.function}] {str(args)[:1500]}")


if __name__ == "__main__":
    main()
