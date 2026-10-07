# RQ2 Data and Condition Audit

## Mapping

| analysis | analysis_name | repo_experiment | status |
| --- | --- | --- | --- |
| A | 来源标签实验 | RQ2/Exp3_ Controlled_Source-Provenance_Intervention | 540 raw runs available; repository processed CSVs were empty, re-extracted here from raw logs |
| B | 基于 RQ1 轨迹的 timing / actual exposure 分析 | Exp1_User_Context_Embedding E and UC_M raw runs | 360 raw runs analyzed descriptively |
| C | 用户安全提示实验 | RQ2/Exp2_SafetyIntent | H1 reused from Exp1 UC_M; H2/H3 new runs; no E+guidance arms found |

## Inclusion Rule

This analysis uses existing completed logs only. It does not launch model calls and does not overwrite source experiment outputs. Runs with valid configs and no recorded runtime error are included. Missing logs would be labeled separately, but the extracted A/B/C trajectory tables contain valid rows only.

## Condition Audit

- A / Controlled Source: 540 valid raw runs, 180 each for C0, C1, and C2. C0 labels M/BM/BW as external; C1 labels only M as user-provided; C2 labels only BM as user-provided. All candidates are placed in a synchronized candidate observation inside a user message.
- B / Timing Exposure: 360 valid raw runs from Exp1, including 180 E and 180 UC_M. E exposure is path-dependent; UC_M exposure is in the initial user message.
- C / User Safety Guidance: 540 valid trajectory rows after joining H1/H2/H3, with 180 per condition. H1 is reused from Exp1 UC_M, H2 appends a concern sentence, and H3 appends an additional verification request. No E-with-guidance condition is present in the default completed data.

## Field Meanings

- Exposure: artifact text appears in model-visible messages.
- Adoption: final selected candidate role in the security/result trace.
- Planning adoption: only retained where an explicit trace flag exists; otherwise marked unknown in trajectory tables.
- Verification: for C H2/H3, safety-trace verification attempt; for A/B, independent verification is not reliably observable and is marked unknown.
- Execution: an artifact-linked `apply_offer`/environment event, not a verbal recommendation.
- Attack success: experiment-specific registered M success flag; not a real-world harm claim.
