# Experiment configs

One YAML file per experiment. The file name is the experiment's name: real runs
write to `logs/<name>/`, pilot runs (`--limit`) to `logs/pilot/<name>/`.

```bash
python scripts/run_experiment.py configs/qwen3_humanevalplus_agent.yaml --limit 5   # pilot
python scripts/run_experiment.py configs/qwen3_humanevalplus_agent.yaml             # full run
python scripts/run_experiment.py configs/*.yaml --dry-run                            # check only
python scripts/run_experiment.py --retry logs/<name>/<file>.eval                     # resume a stopped run
```

A resumed run reuses the tasks that already finished, so they aren't paid for twice. It
writes a new log next to the old one: delete the old one afterwards, or tasks get
counted twice. Use `--retry` rather than `inspect eval-retry`: the plain Inspect
command can't find this project's tasks.

## Fields

| Key | Required | Meaning |
|---|---|---|
| `task` | yes | The Inspect `@task` function, as `module.path:function` |
| `task_args` | no | Arguments passed to that function |
| `model` | yes | Inspect model string, e.g. `ollama/qwen3:14b` |
| `generate` | no | Inspect `GenerateConfig` fields: `temperature`, `reasoning_effort`, `extra_body`, ... |
| `eval` | no | Other `inspect_ai.eval()` options: `epochs`, `max_connections`, `max_samples`, ... |
| `meta` | yes | `model`, `benchmark`, `split`, `setting`, `reasoning`. Saved in the log header; analysis groups runs by these |

Unknown keys are rejected, so a typo fails before anything runs.

## Naming

`<model>_<benchmark>[_<split>]_<setting>[_<reasoning>]`, for example
`qwen3_impossible_lcb_oneoff_single_nothink`. Leave out the reasoning part for
the model's default setting.

## Qwen3 thinking in Ollama

Thinking is on by default. To turn it off, use the `generate.extra_body` block in
`qwen3_humanevalplus_agent_nothink.yaml`. Inspect's own `reasoning_effort: none`
is dropped before it reaches Ollama, and `think: false` is ignored by Ollama's
OpenAI-compatible endpoint.

## Still to add

Configs for Impossible-LCB, once those tasks exist.
