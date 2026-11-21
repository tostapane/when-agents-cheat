"""File templates shared by the HumanEval-style solvers and scorers."""


def build_test_file(test: str, entry_point: str) -> str:
    """Match the test.py written by the ImpossibleBench agent."""
    test_content = test.replace("def check(", "def test_func(")
    return f"""from func import {entry_point}

{test_content}

if __name__ == "__main__":
    test_func({entry_point})
    print("All tests passed!")
"""


def build_single_turn_func_file(prompt: str, code: str) -> str:
    """Keep the prompt's imports and helpers before the model's implementation."""
    return prompt + "\n    pass\n\n" + code + "\n"
