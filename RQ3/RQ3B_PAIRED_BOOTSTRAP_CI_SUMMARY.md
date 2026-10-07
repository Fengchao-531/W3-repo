# RQ3-B Paired Bootstrap CI Results

Bootstrap: 10,000 percentile replicates; seed `20261002`. Sampling unit is base task cluster. Each resample keeps the paired defense-baseline and E-UC records together.

Matching note: Exp1 no-defense baseline does not contain `candidate_order` or `seed`, so complete matching uses `model + pair_id + source`; bootstrap clusters use `base_task` / `base_task_id`. For the four completed models, all M-condition comparisons have 180 matched pairs per model and 20 base-task clusters.

## Table 1: Defense vs No-Defense Baseline, M Conditions

| Model | Defense | Source | Matched N | Base Tasks | Delta Action [95% CI] | Delta Utility [95% CI] | Delta Safe Completion [95% CI] |
|---|---|---|---:|---:|---:|---:|---:|
| Gemma | StruQ | E | 180 | 20 | +1.67 pp [+0.00 pp, +5.00 pp] | -8.33 pp [-20.00 pp, +2.22 pp] | -8.33 pp [-20.00 pp, +2.22 pp] |
| Gemma | StruQ | UC | 180 | 20 | -8.33 pp [-15.00 pp, -2.22 pp] | -0.56 pp [-12.78 pp, +10.00 pp] | +1.67 pp [-9.44 pp, +11.67 pp] |
| Gemma | SecAlign | E | 180 | 20 | +0.00 pp [+0.00 pp, +0.00 pp] | -7.78 pp [-23.33 pp, +5.56 pp] | -7.78 pp [-23.33 pp, +5.56 pp] |
| Gemma | SecAlign | UC | 180 | 20 | -13.33 pp [-23.33 pp, -5.00 pp] | -3.33 pp [-15.00 pp, +7.78 pp] | -1.11 pp [-10.56 pp, +8.89 pp] |
| Gemma | DataSentinel-D | E | 180 | 20 | +2.22 pp [+0.00 pp, +6.11 pp] | -3.33 pp [-13.33 pp, +6.67 pp] | -3.33 pp [-13.33 pp, +6.67 pp] |
| Gemma | DataSentinel-D | UC | 180 | 20 | -2.22 pp [-8.33 pp, +3.89 pp] | -3.89 pp [-16.11 pp, +7.78 pp] | -2.22 pp [-12.78 pp, +7.78 pp] |
| Gemma | CausalArmor | E | 180 | 20 | +0.56 pp [+0.00 pp, +1.67 pp] | +0.56 pp [-3.33 pp, +6.11 pp] | +0.56 pp [-3.33 pp, +6.11 pp] |
| Gemma | CausalArmor | UC | 180 | 20 | +3.89 pp [-3.89 pp, +12.78 pp] | -0.56 pp [-13.33 pp, +12.22 pp] | +1.11 pp [-10.00 pp, +12.22 pp] |
| Llama3.1 | StruQ | E | 180 | 20 | +4.44 pp [-5.00 pp, +14.44 pp] | -6.11 pp [-15.56 pp, +0.00 pp] | -6.11 pp [-15.56 pp, +0.00 pp] |
| Llama3.1 | StruQ | UC | 180 | 20 | -1.67 pp [-12.22 pp, +8.89 pp] | -3.33 pp [-8.33 pp, +0.56 pp] | -2.78 pp [-7.22 pp, +0.00 pp] |
| Llama3.1 | SecAlign | E | 180 | 20 | +5.56 pp [-3.33 pp, +15.00 pp] | -6.11 pp [-15.56 pp, +0.00 pp] | -6.11 pp [-15.56 pp, +0.00 pp] |
| Llama3.1 | SecAlign | UC | 180 | 20 | +6.67 pp [-5.00 pp, +17.78 pp] | -3.89 pp [-8.33 pp, +0.00 pp] | -2.78 pp [-7.22 pp, +0.00 pp] |
| Llama3.1 | DataSentinel-D | E | 180 | 20 | +3.89 pp [-6.11 pp, +15.00 pp] | -6.11 pp [-15.56 pp, +0.00 pp] | -6.11 pp [-15.00 pp, +0.00 pp] |
| Llama3.1 | DataSentinel-D | UC | 180 | 20 | -0.56 pp [-10.56 pp, +10.56 pp] | -3.89 pp [-8.33 pp, +0.00 pp] | -2.78 pp [-7.22 pp, +0.00 pp] |
| Llama3.1 | CausalArmor | E | 180 | 20 | +11.67 pp [+0.00 pp, +23.89 pp] | -5.56 pp [-15.00 pp, +1.11 pp] | -5.56 pp [-15.00 pp, +1.11 pp] |
| Llama3.1 | CausalArmor | UC | 180 | 20 | +2.22 pp [-6.11 pp, +9.44 pp] | -3.89 pp [-8.33 pp, +0.00 pp] | -2.78 pp [-6.67 pp, +0.00 pp] |
| Mistral | StruQ | E | 180 | 20 | +0.00 pp [+0.00 pp, +0.00 pp] | +0.00 pp [+0.00 pp, +0.00 pp] | +0.00 pp [+0.00 pp, +0.00 pp] |
| Mistral | StruQ | UC | 180 | 20 | -1.67 pp [-5.56 pp, +1.11 pp] | +0.00 pp [+0.00 pp, +0.00 pp] | +0.00 pp [+0.00 pp, +0.00 pp] |
| Mistral | SecAlign | E | 180 | 20 | +0.00 pp [+0.00 pp, +0.00 pp] | +0.00 pp [+0.00 pp, +0.00 pp] | +0.00 pp [+0.00 pp, +0.00 pp] |
| Mistral | SecAlign | UC | 180 | 20 | -1.11 pp [-3.33 pp, +0.00 pp] | +0.00 pp [+0.00 pp, +0.00 pp] | +0.00 pp [+0.00 pp, +0.00 pp] |
| Mistral | DataSentinel-D | E | 180 | 20 | +0.56 pp [+0.00 pp, +1.67 pp] | +0.56 pp [+0.00 pp, +1.67 pp] | +0.56 pp [+0.00 pp, +1.67 pp] |
| Mistral | DataSentinel-D | UC | 180 | 20 | -0.56 pp [-3.33 pp, +1.67 pp] | +0.00 pp [+0.00 pp, +0.00 pp] | +0.00 pp [+0.00 pp, +0.00 pp] |
| Mistral | CausalArmor | E | 180 | 20 | -0.56 pp [-1.67 pp, +0.00 pp] | -0.56 pp [-1.67 pp, +0.00 pp] | -0.56 pp [-1.67 pp, +0.00 pp] |
| Mistral | CausalArmor | UC | 180 | 20 | -1.67 pp [-5.00 pp, +0.00 pp] | +0.00 pp [+0.00 pp, +0.00 pp] | +0.00 pp [+0.00 pp, +0.00 pp] |
| Qwen | StruQ | E | 180 | 20 | -3.33 pp [-8.89 pp, +0.56 pp] | -2.78 pp [-9.44 pp, +2.78 pp] | -2.22 pp [-8.89 pp, +3.89 pp] |
| Qwen | StruQ | UC | 180 | 20 | -5.00 pp [-16.11 pp, +5.00 pp] | -3.33 pp [-11.11 pp, +4.44 pp] | +0.56 pp [-6.67 pp, +7.78 pp] |
| Qwen | SecAlign | E | 180 | 20 | -4.44 pp [-11.11 pp, +0.00 pp] | +7.22 pp [-2.22 pp, +17.78 pp] | +7.78 pp [-2.22 pp, +18.89 pp] |
| Qwen | SecAlign | UC | 180 | 20 | +0.00 pp [-12.22 pp, +12.22 pp] | -1.67 pp [-8.33 pp, +4.44 pp] | +2.22 pp [-3.89 pp, +8.35 pp] |
| Qwen | DataSentinel-D | E | 180 | 20 | -5.56 pp [-13.89 pp, -0.56 pp] | +2.78 pp [-4.44 pp, +10.00 pp] | +3.33 pp [-3.89 pp, +10.56 pp] |
| Qwen | DataSentinel-D | UC | 180 | 20 | -2.22 pp [-13.33 pp, +7.22 pp] | +0.56 pp [-7.22 pp, +8.89 pp] | +3.89 pp [-3.33 pp, +11.67 pp] |
| Qwen | CausalArmor | E | 180 | 20 | -5.00 pp [-14.44 pp, +0.56 pp] | +3.33 pp [-3.89 pp, +11.11 pp] | +3.89 pp [-4.44 pp, +12.78 pp] |
| Qwen | CausalArmor | UC | 180 | 20 | -1.11 pp [-12.78 pp, +10.00 pp] | +0.00 pp [-7.78 pp, +8.33 pp] | +2.78 pp [-2.22 pp, +8.89 pp] |

## Table 2: Defense-Condition UC-E Action Gap

| Model | Defense | E Action | UC Action | Matched N | Base Tasks | UC-E Gap [95% CI] |
|---|---|---:|---:|---:|---:|---:|
| Gemma | No defense reference | 0.56% | 16.11% | 180 | 20 | +15.56 pp [+6.67 pp, +25.56 pp] |
| Gemma | StruQ | 2.22% | 7.78% | 180 | 20 | +5.56 pp [-0.56 pp, +12.24 pp] |
| Gemma | SecAlign | 0.56% | 2.78% | 180 | 20 | +2.22 pp [+0.00 pp, +6.11 pp] |
| Gemma | DataSentinel-D | 2.78% | 13.89% | 180 | 20 | +11.11 pp [+2.78 pp, +21.11 pp] |
| Gemma | CausalArmor | 1.11% | 20.00% | 180 | 20 | +18.89 pp [+8.89 pp, +29.44 pp] |
| Llama3.1 | No defense reference | 20.00% | 68.33% | 180 | 20 | +48.33 pp [+32.22 pp, +64.44 pp] |
| Llama3.1 | StruQ | 24.44% | 66.67% | 180 | 20 | +42.22 pp [+30.56 pp, +54.44 pp] |
| Llama3.1 | SecAlign | 25.56% | 75.00% | 180 | 20 | +49.44 pp [+36.11 pp, +62.22 pp] |
| Llama3.1 | DataSentinel-D | 23.89% | 67.78% | 180 | 20 | +43.89 pp [+31.11 pp, +57.22 pp] |
| Llama3.1 | CausalArmor | 31.67% | 70.56% | 180 | 20 | +38.89 pp [+25.00 pp, +53.33 pp] |
| Mistral | No defense reference | 6.67% | 18.89% | 180 | 20 | +12.22 pp [+2.22 pp, +23.89 pp] |
| Mistral | StruQ | 6.67% | 17.22% | 180 | 20 | +10.56 pp [+1.11 pp, +21.67 pp] |
| Mistral | SecAlign | 6.67% | 17.78% | 180 | 20 | +11.11 pp [+1.11 pp, +22.78 pp] |
| Mistral | DataSentinel-D | 7.22% | 18.33% | 180 | 20 | +11.11 pp [+0.56 pp, +23.33 pp] |
| Mistral | CausalArmor | 6.11% | 17.22% | 180 | 20 | +11.11 pp [+1.67 pp, +22.22 pp] |
| Qwen | No defense reference | 6.67% | 41.67% | 180 | 20 | +35.00 pp [+23.89 pp, +47.22 pp] |
| Qwen | StruQ | 3.33% | 36.67% | 180 | 20 | +33.33 pp [+23.33 pp, +43.89 pp] |
| Qwen | SecAlign | 2.22% | 41.67% | 180 | 20 | +39.44 pp [+28.88 pp, +50.56 pp] |
| Qwen | DataSentinel-D | 1.11% | 39.44% | 180 | 20 | +38.33 pp [+27.22 pp, +50.00 pp] |
| Qwen | CausalArmor | 1.67% | 40.56% | 180 | 20 | +38.89 pp [+28.33 pp, +49.44 pp] |

## Table 3: Source Interaction, Action Metric

| Model | Defense | UC Def-Base | E Def-Base | Matched N | Base Tasks | Interaction [95% CI] |
|---|---|---:|---:|---:|---:|---:|
| Gemma | StruQ | -8.33 pp | +1.67 pp | 180 | 20 | -10.00 pp [-18.89 pp, -2.22 pp] |
| Gemma | SecAlign | -13.33 pp | +0.00 pp | 180 | 20 | -13.33 pp [-23.33 pp, -5.00 pp] |
| Gemma | DataSentinel-D | -2.22 pp | +2.22 pp | 180 | 20 | -4.44 pp [-11.11 pp, +2.22 pp] |
| Gemma | CausalArmor | +3.89 pp | +0.56 pp | 180 | 20 | +3.33 pp [-4.44 pp, +12.22 pp] |
| Llama3.1 | StruQ | -1.67 pp | +4.44 pp | 180 | 20 | -6.11 pp [-20.00 pp, +7.22 pp] |
| Llama3.1 | SecAlign | +6.67 pp | +5.56 pp | 180 | 20 | +1.11 pp [-13.33 pp, +15.00 pp] |
| Llama3.1 | DataSentinel-D | -0.56 pp | +3.89 pp | 180 | 20 | -4.44 pp [-17.22 pp, +8.33 pp] |
| Llama3.1 | CausalArmor | +2.22 pp | +11.67 pp | 180 | 20 | -9.44 pp [-25.00 pp, +5.56 pp] |
| Mistral | StruQ | -1.67 pp | +0.00 pp | 180 | 20 | -1.67 pp [-5.56 pp, +1.11 pp] |
| Mistral | SecAlign | -1.11 pp | +0.00 pp | 180 | 20 | -1.11 pp [-3.33 pp, +0.00 pp] |
| Mistral | DataSentinel-D | -0.56 pp | +0.56 pp | 180 | 20 | -1.11 pp [-3.89 pp, +1.11 pp] |
| Mistral | CausalArmor | -1.67 pp | -0.56 pp | 180 | 20 | -1.11 pp [-5.00 pp, +1.67 pp] |
| Qwen | StruQ | -5.00 pp | -3.33 pp | 180 | 20 | -1.67 pp [-12.78 pp, +8.33 pp] |
| Qwen | SecAlign | +0.00 pp | -4.44 pp | 180 | 20 | +4.44 pp [-9.44 pp, +17.78 pp] |
| Qwen | DataSentinel-D | -2.22 pp | -5.56 pp | 180 | 20 | +3.33 pp [-10.00 pp, +16.11 pp] |
| Qwen | CausalArmor | -1.11 pp | -5.00 pp | 180 | 20 | +3.89 pp [-9.44 pp, +16.67 pp] |

## Pooled Results

Pooled CIs are in `rq3b_pooled_ci.csv`. They resample synchronized `base_task` clusters and include all four model records and all pair IDs under each sampled task. These describe the four tested models, not all LLMs.

| Analysis | Defense | Source | Metric | N pairs | Base-task clusters | Delta [95% CI] |
|---|---|---|---|---:|---:|---:|
| defense_vs_baseline | StruQ | E | action | 720 | 20 | +0.69 pp [-2.36 pp, +3.89 pp] |
| defense_vs_baseline | StruQ | E | utility | 720 | 20 | -4.31 pp [-7.50 pp, -1.11 pp] |
| defense_vs_baseline | StruQ | E | safe_completion | 720 | 20 | -4.17 pp [-7.36 pp, -0.97 pp] |
| defense_vs_baseline | StruQ | UC | action | 720 | 20 | -4.17 pp [-8.33 pp, +0.14 pp] |
| defense_vs_baseline | StruQ | UC | utility | 720 | 20 | -1.81 pp [-5.56 pp, +1.67 pp] |
| defense_vs_baseline | StruQ | UC | safe_completion | 720 | 20 | -0.14 pp [-3.61 pp, +3.19 pp] |
| defense_vs_baseline | SecAlign | E | action | 720 | 20 | +0.28 pp [-2.50 pp, +2.92 pp] |
| defense_vs_baseline | SecAlign | E | utility | 720 | 20 | -1.67 pp [-5.42 pp, +2.08 pp] |
| defense_vs_baseline | SecAlign | E | safe_completion | 720 | 20 | -1.53 pp [-5.28 pp, +2.22 pp] |
| defense_vs_baseline | SecAlign | UC | action | 720 | 20 | -1.94 pp [-5.69 pp, +1.81 pp] |
| defense_vs_baseline | SecAlign | UC | utility | 720 | 20 | -2.22 pp [-5.42 pp, +1.11 pp] |
| defense_vs_baseline | SecAlign | UC | safe_completion | 720 | 20 | -0.42 pp [-3.33 pp, +2.64 pp] |
| defense_vs_baseline | DataSentinel-D | E | action | 720 | 20 | +0.28 pp [-3.47 pp, +4.03 pp] |
| defense_vs_baseline | DataSentinel-D | E | utility | 720 | 20 | -1.53 pp [-5.00 pp, +1.94 pp] |
| defense_vs_baseline | DataSentinel-D | E | safe_completion | 720 | 20 | -1.39 pp [-5.00 pp, +2.08 pp] |
| defense_vs_baseline | DataSentinel-D | UC | action | 720 | 20 | -1.39 pp [-6.11 pp, +3.75 pp] |
| defense_vs_baseline | DataSentinel-D | UC | utility | 720 | 20 | -1.81 pp [-5.56 pp, +1.94 pp] |
| defense_vs_baseline | DataSentinel-D | UC | safe_completion | 720 | 20 | -0.28 pp [-3.61 pp, +3.06 pp] |
| defense_vs_baseline | CausalArmor | E | action | 720 | 20 | +1.67 pp [-2.36 pp, +5.69 pp] |
| defense_vs_baseline | CausalArmor | E | utility | 720 | 20 | -0.56 pp [-3.75 pp, +2.50 pp] |
| defense_vs_baseline | CausalArmor | E | safe_completion | 720 | 20 | -0.42 pp [-3.61 pp, +2.78 pp] |
| defense_vs_baseline | CausalArmor | UC | action | 720 | 20 | +0.83 pp [-3.75 pp, +5.00 pp] |
| defense_vs_baseline | CausalArmor | UC | utility | 720 | 20 | -1.11 pp [-5.14 pp, +3.19 pp] |
| defense_vs_baseline | CausalArmor | UC | safe_completion | 720 | 20 | +0.28 pp [-2.92 pp, +3.61 pp] |
| source_gap_uc_minus_e_action | No defense reference | UC-E | action | 720 | 20 | +27.78 pp [+22.22 pp, +32.92 pp] |
| source_gap_uc_minus_e_action | StruQ | UC-E | action | 720 | 20 | +22.92 pp [+18.33 pp, +27.64 pp] |
| source_gap_uc_minus_e_action | SecAlign | UC-E | action | 720 | 20 | +25.56 pp [+20.56 pp, +30.69 pp] |
| source_gap_uc_minus_e_action | DataSentinel-D | UC-E | action | 720 | 20 | +26.11 pp [+20.00 pp, +32.64 pp] |
| source_gap_uc_minus_e_action | CausalArmor | UC-E | action | 720 | 20 | +26.94 pp [+20.83 pp, +32.78 pp] |
| source_interaction_action | StruQ | interaction | action | 720 | 20 | -4.86 pp [-9.72 pp, -0.14 pp] |
| source_interaction_action | SecAlign | interaction | action | 720 | 20 | -2.22 pp [-7.08 pp, +2.64 pp] |
| source_interaction_action | DataSentinel-D | interaction | action | 720 | 20 | -1.67 pp [-7.36 pp, +4.31 pp] |
| source_interaction_action | CausalArmor | interaction | action | 720 | 20 | -0.83 pp [-6.39 pp, +4.86 pp] |

## BM Supplement

BM supplement results are in `rq3b_bm_supplement_ci.csv`. UC_BM rows have formal paired CIs. E_BM rows are descriptive only because the no-defense reference is extracted from Exp1 E runs rather than an explicit matched no-defense E_BM condition.

## Output Files

- `rq3b_defense_vs_baseline_ci.csv`
- `rq3b_source_gap_ci.csv`
- `rq3b_source_interaction_ci.csv`
- `rq3b_bm_supplement_ci.csv`
- `rq3b_pooled_ci.csv`
