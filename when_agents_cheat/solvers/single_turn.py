"""Prepare a single model completion for the file-based scorers."""

import re

from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import sandbox, store

from when_agents_cheat.workspace import build_single_turn_func_file, build_test_file

FENCE = re.compile(r"```[^\n`]*\n(.*?)```", re.DOTALL)


def extract_code(completion: str) -> tuple[str, bool]:
    """Use the last fenced block or fall back to the completion text."""
    completion = re.sub(r"<think>.*?</think>", "", completion, flags=re.DOTALL)
    blocks = FENCE.findall(completion)
    return (blocks[-1], True) if blocks else (completion, False)


@solver
def write_solution_files() -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        code, found = extract_code(state.output.completion if state.output else "")
        metadata = state.metadata
        await sandbox().write_file("func.py", build_single_turn_func_file(metadata["prompt"], code))
        await sandbox().write_file("test.py", build_test_file(metadata["test"], metadata["entry_point"]))
        store().set("code_block_found", found)
        return state

    return solve
