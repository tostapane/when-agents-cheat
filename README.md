# When Agents Cheat: Benchmarking Reward Hacking

We measure how often coding models cheat on normal tasks (HumanEval+) and
impossible tasks (ImpossibleBench), in single-turn and agent settings, using
Qwen3-14B and DeepSeek-V4.1-Flash.

## Setup

You need [uv](https://docs.astral.sh/uv/) (`pip install uv`) and Docker. Both
options below install the exact package versions in `uv.lock`.

### Using a venv

```bash
uv sync
source .venv/bin/activate
```

`uv sync` creates the `.venv` inside the repo and downloads Python 3.12 if needed.

### Using conda

Create a new environment for this project, because `uv sync --active` removes
any packages that aren't in `uv.lock`.

```bash
conda create -n when-agents-cheat python=3.12
conda activate when-agents-cheat
pip install uv
uv sync --active
```

## Changing dependencies

Don't use `pip install` or `conda install` for this project's packages. Run
`uv add <package>`, then commit `pyproject.toml` and `uv.lock`. After pulling
changes to either file, repeat the `uv sync` command you used during setup.

## Structure

Inspect AI runs every experiment. A run reads its settings from `configs/`,
runs a benchmark task with the model's code inside the Docker sandbox, then
checks the result and saves everything to `logs/`.

```
when-agents-cheat/
├── when_agents_cheat/      # Code shared by the whole project
│   ├── tasks/              # One file per benchmark: loads its tasks and sets up each run
│   ├── sandbox/            # Docker setup for the container that runs model-written code
│   ├── scorers/            # Runs the hidden tests after the agent finishes
│   └── detectors/          # Cheating checks: failed hidden tests, "passed" impossible
│                           # tasks, edited test files, test-specific logic
├── serving/qwen3/          # Serves Qwen on the GPU machine, in its own environment
├── configs/                # One file per experiment: model, benchmark, setting, limits
├── scripts/                # Commands that start experiments
├── analysis/               # Turns logs into tables and plots
├── labeling/               # Labeling guide, sampled cases and manual labels
├── data/                   # Downloaded datasets (local only, not committed)
├── logs/                   # Raw run outputs (local only, not committed)
├── pyproject.toml          # The packages this project needs
└── uv.lock                 # The exact version of every package
```
