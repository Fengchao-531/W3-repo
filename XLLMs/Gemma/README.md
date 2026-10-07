# Gemma W3 runs

Set `GEMMA_MODEL_PATH` to a local instruction-tuned Gemma snapshot. Results,
full prompts/traces, hidden states, completion markers, and the tracker manifest
are written in this directory.

```bash
export GEMMA_MODEL_PATH=/path/to/gemma-instruct/snapshot
bash run.sh exp1
bash run.sh exp3
```
