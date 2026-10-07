# RQ3 Controlled Verification

This folder adds the required RQ3-A `E_M_H3` condition.

The dataset reuses Exp1 base tasks, candidate artifacts, candidate order, external representation, tool environment, and H3 wording. The only new intervention is appending the same H3 concern and explicit verification request used by RQ2 SafetyIntent to the external H1 user task.

Run outputs are written by model name:

`02_runs/E_M_H3/<model>/<run_id>/`

Each completed run has `15_trace_summary.json` and is skipped on resume unless `--force` is passed.
