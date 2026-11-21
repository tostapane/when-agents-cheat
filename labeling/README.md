# Labeling

`cases.csv` has one row per suspect case: a sample the automatic checks flagged as possible cheating.
The labels and the rule for `cheating` are defined in `DECISIONS.md` ("Manual labeling").

| Column | Meaning |
|---|---|
| `case` | Row number |
| `run` | The run's folder in `logs/`, e.g. `deepseek_humanevalplus_agent` |
| `task`, `epoch` | Which sample. See it with `python analysis/show_sample.py <run> <task> <epoch>` |
| `why_flagged` | Which automatic check flagged it: `hidden fail` or `hidden timeout` (all of these passed the visible tests) |
| `failed_inputs` | How many hidden inputs fail, out of all of them. A few means an edge case; nearly all suggests hardcoding |
| `label` | One of the 8 labels |
| `cheating` | `yes` or `no`, following from the label |
| `labeler` | Who labeled it |
| `notes` | One line on why |

To add cases from a new run (e.g. Impossible-LCB), append rows with the same columns.
