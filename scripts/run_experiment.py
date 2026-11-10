"""Runs one or more experiments, each described by a YAML file in configs/.

Run from the repo root:

    python scripts/run_experiment.py configs/qwen3_humanevalplus_agent.yaml
    python scripts/run_experiment.py configs/qwen3_*.yaml          # several, one after another
    python scripts/run_experiment.py configs/qwen3_humanevalplus_agent.yaml --limit 5   # pilot

Real runs write to logs/<config name>/. Runs with --limit are pilots and write to
logs/pilot/<config name>/, so they never mix with the real results.

Config format (see configs/README.md for the details):

    task: module.path:function     # an Inspect @task function
    task_args: {...}               # arguments for that function
    model: provider/model-name     # any Inspect model string
    generate: {...}                # Inspect GenerateConfig fields (optional)
    eval: {...}                    # extra inspect_ai.eval() options (optional)
    meta: {model, benchmark, split, setting, reasoning}   # copied into the log
"""

import argparse
import importlib
import inspect
import sys
from pathlib import Path

import yaml
from inspect_ai import eval as inspect_eval
from inspect_ai.model import GenerateConfig

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_ROOT = REPO_ROOT / "logs"

TOP_LEVEL_KEYS = {"task", "task_args", "model", "generate", "eval", "meta"}
REQUIRED_KEYS = {"task", "model", "meta"}

# Every run records these, so analysis can group runs without parsing file names.
META_KEYS = {"model", "benchmark", "split", "setting", "reasoning"}

# Options in `eval:` must be real inspect_ai.eval() parameters. These ones are set
# by this script instead, so a config can't override them.
EVAL_KEYS_SET_HERE = {"tasks", "model", "log_dir", "metadata", "tags", "limit"}
ALLOWED_GENERATE_KEYS = set(GenerateConfig.model_fields)
# Some run options, like max_connections, are GenerateConfig fields in Inspect,
# so `eval:` accepts those too.
ALLOWED_EVAL_KEYS = (
    set(inspect.signature(inspect_eval).parameters) - EVAL_KEYS_SET_HERE - {"kwargs"}
) | ALLOWED_GENERATE_KEYS


class ConfigError(Exception):
    pass


def load_config(path: Path) -> dict:
    with open(path, encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise ConfigError(f"{path}: expected a YAML mapping at the top level")

    # Unknown keys are almost always typos, which would otherwise be ignored silently.
    check_keys(path, "top level", config, allowed=TOP_LEVEL_KEYS, required=REQUIRED_KEYS)
    check_keys(path, "meta", config["meta"], allowed=META_KEYS, required=META_KEYS)
    check_keys(path, "generate", config.get("generate") or {}, allowed=ALLOWED_GENERATE_KEYS)
    check_keys(path, "eval", config.get("eval") or {}, allowed=ALLOWED_EVAL_KEYS)
    return config


def check_keys(path: Path, section: str, values: dict, allowed: set, required: set = frozenset()):
    if not isinstance(values, dict):
        raise ConfigError(f"{path}: `{section}` must be a mapping")
    unknown = set(values) - allowed
    missing = set(required) - set(values)
    if unknown:
        raise ConfigError(f"{path}: unknown key(s) in {section}: {sorted(unknown)}")
    if missing:
        raise ConfigError(f"{path}: missing key(s) in {section}: {sorted(missing)}")


def build_task(spec: str, task_args: dict):
    """Imports `module.path:function` and calls it, which returns an Inspect Task."""
    module_name, _, function_name = spec.partition(":")
    if not function_name:
        raise ConfigError(f"task must look like 'module.path:function', got {spec!r}")
    task_function = getattr(importlib.import_module(module_name), function_name)
    return task_function(**task_args)


def run(path: Path, limit: int | None, dry_run: bool) -> bool:
    config = load_config(path)
    name = path.stem
    log_dir = LOG_ROOT / "pilot" / name if limit is not None else LOG_ROOT / name

    print(f"\n=== {name} ===")
    print(f"model: {config['model']}")
    print(f"task:  {config['task']} {config.get('task_args') or {}}")
    print(f"logs:  {log_dir.relative_to(REPO_ROOT)}")
    if dry_run:
        return True

    task = build_task(config["task"], config.get("task_args") or {})
    logs = inspect_eval(
        task,
        model=config["model"],
        log_dir=str(log_dir),
        limit=limit,
        # Stored in the log header, so analysis/ can read them back.
        metadata={**config["meta"], "config_name": name, "config": config},
        tags=[name],
        **(config.get("eval") or {}),
        **(config.get("generate") or {}),
    )
    return all(log.status == "success" for log in logs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("configs", nargs="+", type=Path, help="YAML files in configs/")
    parser.add_argument("--limit", type=int, help="run only the first N tasks (pilot run)")
    parser.add_argument("--dry-run", action="store_true", help="check the configs without running anything")
    args = parser.parse_args()

    # Check every config first, so a typo in the last one doesn't surface hours later.
    try:
        for path in args.configs:
            load_config(path)
    except (ConfigError, OSError, yaml.YAMLError) as error:
        print(f"Config error: {error}", file=sys.stderr)
        return 2

    failed = [path.stem for path in args.configs if not run(path, args.limit, args.dry_run)]
    if failed:
        print(f"\nNot successful: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
