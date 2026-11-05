"""Runs the datasets' reference solutions against their tests, with no model involved.

Run this inside the sandbox image, from the repo root. It writes nothing to the repo:

    docker run --rm --network none --memory 4g \
      -v "$PWD/data:/data:ro" -v "$PWD/scripts:/scripts:ro" \
      when-agents-cheat-sandbox python -I /scripts/check_reference_solutions.py
"""

import gzip
import json
import os
import signal
import statistics
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

HE_PATH = "/data/humaneval/HumanEval.jsonl.gz"
HEP_PATH = "/data/humanevalplus/HumanEvalPlus-OriginFmt.jsonl.gz"

TIMEOUT_SECONDS = 120  # Well above the authors' 30s, so slow tests get measured.
AUTHORS_LIMIT_SECONDS = 30
MEMORY_LIMIT_MB = 1024  # The per-container limit in sandbox/compose.yaml.
WORKERS = 4
MAX_FAILURES_SHOWN = 15


def load(path):
    with gzip.open(path, "rt") as f:
        return {row["task_id"]: row for row in map(json.loads, f)}


def build_test_file(test_code, entry_point):
    """Same layout as the test.py the authors' agent creates."""
    test_code = test_code.replace("def check(", "def test_func(")
    return f"""from func import {entry_point}

{test_code}

if __name__ == "__main__":
    test_func({entry_point})
    print("All tests passed!")
"""


def run_python(workdir):
    """Runs test.py and returns (exit status or None on timeout, seconds, peak MB)."""
    command = f"cd {workdir} && exec python test.py >/dev/null 2>stderr.txt"
    pid = os.spawnlp(os.P_NOWAIT, "sh", "sh", "-c", command)
    start = time.time()
    while True:
        done, status, usage = os.wait4(pid, os.WNOHANG)
        seconds = time.time() - start
        if done:
            return os.waitstatus_to_exitcode(status), seconds, usage.ru_maxrss / 1024
        if seconds > TIMEOUT_SECONDS:
            os.kill(pid, signal.SIGKILL)
            _, _, usage = os.wait4(pid, 0)
            return None, seconds, usage.ru_maxrss / 1024
        time.sleep(0.02)


def check(job):
    solutions, tests, task_id = job
    solution, test = solutions[task_id], tests[task_id]
    with tempfile.TemporaryDirectory() as workdir:
        with open(f"{workdir}/func.py", "w") as f:
            f.write(solution["prompt"] + solution["canonical_solution"])
        with open(f"{workdir}/test.py", "w") as f:
            f.write(build_test_file(test["test"], solution["entry_point"]))
        code, seconds, peak_mb = run_python(workdir)
        with open(f"{workdir}/stderr.txt", errors="replace") as f:
            lines = f.read().strip().splitlines()
    error = f"timed out after {TIMEOUT_SECONDS}s" if code is None else (lines[-1][:100] if lines else f"exit {code}")
    return task_id, code == 0, seconds, peak_mb, error


def main():
    he, hep = load(HE_PATH), load(HEP_PATH)
    combinations = [
        ("HumanEval+ solutions vs visible tests", hep, he),
        ("HumanEval+ solutions vs full HumanEval+ tests", hep, hep),
        ("Original solutions vs visible tests", he, he),
        ("Original solutions vs full HumanEval+ tests", he, hep),
    ]
    with ThreadPoolExecutor(WORKERS) as pool:
        for name, solutions, tests in combinations:
            results = list(pool.map(check, [(solutions, tests, task_id) for task_id in solutions]))
            failed = [r for r in results if not r[1]]
            times = [r[2] for r in results]
            peaks = [r[3] for r in results]
            print(f"\n== {name}")
            print(f"passed {len(results) - len(failed)}/{len(results)}")
            print(
                f"time: median {statistics.median(times):.2f}s, max {max(times):.1f}s, "
                f"over {AUTHORS_LIMIT_SECONDS}s: {sum(t > AUTHORS_LIMIT_SECONDS for t in times)}"
            )
            print(f"peak memory: max {max(peaks):.0f} MB, over {MEMORY_LIMIT_MB} MB: {sum(p > MEMORY_LIMIT_MB for p in peaks)}")
            for task_id, _, seconds, _, error in failed[:MAX_FAILURES_SHOWN]:
                print(f"  FAIL {task_id} ({seconds:.1f}s): {error}")
            if len(failed) > MAX_FAILURES_SHOWN:
                print(f"  ...and {len(failed) - MAX_FAILURES_SHOWN} more")


if __name__ == "__main__":
    main()
