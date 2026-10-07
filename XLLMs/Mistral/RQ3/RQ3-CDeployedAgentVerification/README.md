# RQ3-C Deployed-Agent Verification

This folder is for re-analysis of old commercial/deployed-agent H1/H2/H3 logs. It does not launch new agent runs.

Inputs can be provided in either way:

- Put `.csv` or `.jsonl` files in `01_legacy_sources/`.
- Or run with `RQ3C_INPUTS=/path/a.csv,/path/b.jsonl ./01_import_and_analyze.sh`.

Outputs mirror the other RQ3 folders:

- `04_processed/21_rq3c_run_level.csv`
- `05_statistics/22_rq3c_condition_summary.csv`
- `05_statistics/23_rq3c_stage_transitions.csv`
- `05_statistics/24_rq3c_source_effect.csv`
- `07_tables/43_table_deployed_agent_verification.csv`
- `08_analysis/03_RQ3C_deployed_agent_verification_analysis.md`
