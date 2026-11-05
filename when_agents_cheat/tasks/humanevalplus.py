"""HumanEval+ as an Inspect task, using the ImpossibleBench authors' tool-based agent.

The model only gets the prompt and the visible tests from the original HumanEval.
Reference solutions and the full HumanEval+ tests never enter the task, so they
can't reach the model. Scoring here uses the visible tests only.

Run from the repo root:

    inspect eval when_agents_cheat/tasks/humanevalplus.py \
        --model deepseek/deepseek-flash --limit 1
"""

import gzip
import json
from pathlib import Path

from impossiblebench.livecodebench_agent_full import swe_bench_style_humaneval_solver
from impossiblebench.livecodebench_scorers import swe_style_humaneval_scorer
from impossiblebench.livecodebench_tasks import INSTRUCTION, INSTRUCTION_SUFFIX_TOOLS
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample

PACKAGE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_DIR.parent / "data"
COMPOSE_FILE = PACKAGE_DIR / "sandbox" / "compose.yaml"

HUMANEVAL_FILE = DATA_DIR / "humaneval" / "HumanEval.jsonl.gz"
HUMANEVALPLUS_FILE = DATA_DIR / "humanevalplus" / "HumanEvalPlus-OriginFmt.jsonl.gz"

# Same wording as the authors' agent on LiveCodeBench, so both benchmarks match.
INSTRUCTION_PROMPT = INSTRUCTION + " **DO NOT MODIFY THE TESTS.**" + INSTRUCTION_SUFFIX_TOOLS

# These visible tests call helpers defined in the prompt, but the agent's test.py
# only imports the entry point. Without this import they fail on any solution.
TASKS_NEEDING_HELPER_IMPORT = {"HumanEval/32", "HumanEval/38", "HumanEval/50"}


def read_tasks(path: Path) -> dict[str, dict]:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run ./scripts/download_data.sh first.")
    with gzip.open(path, "rt") as file:
        return {row["task_id"]: row for row in map(json.loads, file)}


def visible_test(task_id: str, test: str) -> str:
    if task_id in TASKS_NEEDING_HELPER_IMPORT:
        return "from func import *\n" + test
    return test


def load_tasks() -> MemoryDataset:
    original = read_tasks(HUMANEVAL_FILE)
    plus = read_tasks(HUMANEVALPLUS_FILE)

    samples = [
        Sample(
            id=task_id,
            input=INSTRUCTION_PROMPT,
            target="",
            metadata={
                "task_id": task_id,
                # HumanEval+ prompts, because the original HumanEval/115 prompt
                # has `import math` before its docstring.
                "prompt": row["prompt"],
                "test": visible_test(task_id, original[task_id]["test"]),
                "entry_point": row["entry_point"],
                "instruction_prompt": INSTRUCTION_PROMPT,
            },
        )
        for task_id, row in plus.items()
    ]
    return MemoryDataset(samples, name="humanevalplus")


@task
def humanevalplus(max_attempts: int = 10, message_limit: int = 50) -> Task:
    """Runs the agent on HumanEval+ tasks.

    The default limits are the ones in the authors' example. They are provisional:
    `max_attempts` counts submissions and `message_limit` counts messages, and
    neither is the same as the proposal's 10 steps yet.
    """
    return Task(
        dataset=load_tasks(),
        solver=swe_bench_style_humaneval_solver(max_attempts=max_attempts),
        scorer=swe_style_humaneval_scorer(),
        sandbox=("docker", str(COMPOSE_FILE)),
        message_limit=message_limit,
    )
