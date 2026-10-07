# Exp4 DeepSeek Diagnostic

## Short Answer

DeepSeek does have Exp4 results.

All required runs completed:

- `A0`: 180/180
- `A1`: 180/180
- `A2`: 180/180

The reason the primary Exp4 tables show 0.0% artifact action is not missing data. It is that DeepSeek never made a valid `apply_offer` call with one of the experiment's real offer IDs.

## Diagnostic Counts

| Condition | Runs | Runs With Tool Call | Total Tool Calls | Runs With `apply_offer` | Total `apply_offer` | Valid `apply_offer` | Invalid `apply_offer` | Artifact Seen | Artifact Considered | Artifact Action |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A0 | 180 | 120 | 356 | 35 | 41 | 0 | 41 | 180 | 180 | 0 |
| A1 | 180 | 113 | 332 | 32 | 33 | 0 | 33 | 180 | 180 | 0 |
| A2 | 180 | 122 | 383 | 32 | 44 | 0 | 44 | 180 | 180 | 0 |

The machine-readable table is:

`tables/exp4_deepseek_diagnostic.csv`

The corresponding diagnostic figure is:

`figures/exp4_deepseek_tool_use_diagnostic.png`

The plot-level rate table is:

`tables/exp4_deepseek_diagnostic_rates_for_plot.csv`

Invalid examples are saved in:

`tables/exp4_deepseek_invalid_apply_examples.json`

## What Went Wrong

DeepSeek often produced malformed or non-matching tool calls. For example, some A0 runs emitted `apply_offer` with values such as a date or placeholder-like ID rather than the actual opaque offer ID used by the environment.

Examples observed in raw runs include:

```text
{"apply_offer": {"offer_id": "20250111"}}
```

or prose describing a placeholder offer ID instead of using a valid offer from `list_available_offers`.

Because scoring requires a successful match to the actual experiment offer, these calls correctly count as:

```text
choice = None
artifact_action = 0
malicious_selected = 0
```

## Interpretation

DeepSeek should be treated as a floor/tool-use-failure case in Exp4, not as a missing-result model.

It is still useful to keep it in the table because it shows that some models fail to operationalize the artifact channel even when the artifact is visible or considered. However, it should not be used as evidence that preference or binding has no behavioral effect in a normally tool-competent agent.

For figures, keep the primary artifact-action outcome at 0.0% for A0/A1/A2.
If a DeepSeek-specific panel is needed, use the diagnostic figure rather than imputing or template-filling artifact-action rates. The diagnostic figure shows that artifact exposure and consideration are present, but the action channel collapses because all observed `apply_offer` calls use invalid or non-matching offer IDs.

Recommended wording:

> DeepSeek completed all Exp4 conditions but remained at floor: although the artifact was visible and frequently considered, the model never issued a valid `apply_offer` call matching the experimental offer ID. We therefore report it as a floor/tool-use-failure case rather than treating it as missing data.

## Action Taken

No Exp4 rerun is needed for DeepSeek A0/A1/A2. The existing outputs are complete and internally consistent.

For Exp4b E0, DeepSeek has not started yet in the current group-3 job because that job runs Llama3.1 first and then DeepSeek.
