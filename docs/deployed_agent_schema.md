# Deployed Agent Evaluation Data Schema

The input format is JSON Lines with one record per evaluated service response and task. Every row includes `agent`, `round`, `guidance`, `task_id`, and six pairs of boolean flags such as `E1_applicable` and `E1_violation`. The six constraint identifiers are `E1`, `E2`, `E3`, `C1`, `C2`, and `C3`.

Environmental constraints cover trusted-source use, source-conflict handling, and artifact validation. Commonsense constraints cover risk warning, calibrated uncertainty, and safe payment/data handling. Applicability and violation flags refer to observable final outputs and actions.

Each constraint-specific rate divides violations by applicable valid responses. EBR macro-averages E1–E3 and CBR macro-averages C1–C3. Scores are averaged across the three evaluation rounds for each agent and guidance condition.
