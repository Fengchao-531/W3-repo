# W3-repo

## Included DataSentinel Files

This repository now includes the code needed to run the DataSentinel defense under:

- `W3/Detection-Methods/run_datasentinel_prediction_results.py`
- `W3/Detection-Methods/run_datasentinel_prediction_results.sh`
- `W3/Detection-Methods/prepare_prediction_results.py`
- `W3/Detection-Methods/probe_5_samples.py`
- `W3/Detection-Methods/Detection-based/Open-Prompt-Injection/`

Notes:

- The upstream `Open-Prompt-Injection` code is included as a local dependency.
- Large model checkpoints, Hugging Face cache, and prediction result JSONL files are not included.
- Running DataSentinel still requires:
  - a compatible base model
  - a downloaded fine-tuned DataSentinel checkpoint passed via `DATASENTINEL_FT_PATH`
