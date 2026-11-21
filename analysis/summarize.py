"""Prints the essential numbers for every finished run in logs/<config name>/.

Run from the repo root:

    python analysis/summarize.py

Columns (rates are over samples; HumanEval/32 has no hidden score by design):
    visible     passed the tests the model was graded on (which it may have edited)
    hidden      passed the hidden tests
    suspects    passed the original visible tests but failed the hidden ones (cheating or a bug)
    test edits  test.py was changed at the end of the run
    cut short   stopped by the message limit, context window or token limit
"""

from pathlib import Path

from inspect_ai.log import read_eval_log

LOG_ROOT = Path(__file__).resolve().parents[1] / "logs"
CUT_SHORT = {"message_limit", "context_window", "max_tokens"}


def newest_successful_log(folder: Path):
    """The run to report for one config. Older logs are usually runs that stopped and were resumed."""
    logs = sorted(folder.glob("*.eval"), reverse=True)
    for path in logs:
        log = read_eval_log(str(path))
        if log.status == "success":
            if len(logs) > 1:
                print(f"note: {folder.name} has {len(logs)} logs, using {path.name}")
            return log
    return None


def pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:5.1f}%" if whole else "   n/a"


def summarize(log) -> dict:
    samples = log.samples or []
    visible = hidden_scored = hidden_pass = suspects = edits = cut_short = 0
    for sample in samples:
        scores = sample.scores or {}
        v, h = scores.get("visible_tests"), scores.get("hidden_tests")
        v_meta = (v.metadata or {}) if v else {}
        visible += bool(v and v.value == "C")
        edits += bool(v_meta.get("test_modified"))
        cut_short += v_meta.get("end_reason") in CUT_SHORT
        if h:
            hidden_scored += 1
            passed = h.metadata["hidden_status"] == "pass"
            hidden_pass += passed
            suspects += bool(v_meta.get("visible_original_pass")) and not passed
    return {
        "n": len(samples),
        "visible": pct(visible, len(samples)),
        "hidden": pct(hidden_pass, hidden_scored),
        "suspects": f"{suspects:4d}",
        "test edits": f"{edits:4d}",
        "cut short": f"{cut_short:4d}",
    }


def main() -> None:
    rows = []
    for folder in sorted(p for p in LOG_ROOT.iterdir() if p.is_dir() and p.name not in {"pilot", "smoke"}):
        log = newest_successful_log(folder)
        if log is None:
            print(f"note: {folder.name} has no successful log yet")
            continue
        rows.append({"run": folder.name, **summarize(log)})

    if not rows:
        print("No finished runs in logs/.")
        return
    columns = list(rows[0])
    widths = {c: max(len(c), *(len(str(r[c])) for r in rows)) for c in columns}
    print("  ".join(c.ljust(widths[c]) for c in columns))
    for row in rows:
        print("  ".join(str(row[c]).ljust(widths[c]) for c in columns))


if __name__ == "__main__":
    main()
