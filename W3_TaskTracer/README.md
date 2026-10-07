# W3 TaskTracer

GPT-4o behavioral side of RQ2 Reliance Calibration + Propagation. It reuses
`../RQ2Tracker/behavioral_trace.py`, so GPT-4o and open-source models have the
same behavioral fields and annotation rules. GPT-4o rows intentionally report
no internal trace.

```bash
bash run_full.sh
```

Outputs are written to `03_behavioral_traces/` and `04_metrics/`. The older
`run_smoke.sh` remains available for validating the legacy TaskTracer prompt
conversion and is not required for behavioral extraction.
