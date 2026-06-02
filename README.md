# W3-repo

This repository contains the exportable pieces of the local `W3` workspace that are ready to clone on another machine and run.

## Included

- `W3/Detection-Methods/` scripts and prepared prediction-result inputs
- `W3/LLM-Bench/` self-contained benchmark bundle
- selected top-level helper scripts and datasets used by the exported workflows

## LLM-Bench

`W3/LLM-Bench/` is organized so it can be cloned on `csiro` and run directly:

- benchmark inputs are bundled under `W3/LLM-Bench/datasets/`
- completed `M3` benchmark outputs are kept under `W3/LLM-Bench/result/M3/`
- new `CSIRO` runs write to `W3/LLM-Bench/result/CSIRO/` and are ignored by Git

Start from:

- `W3/LLM-Bench/README.md`
- `W3/LLM-Bench/run_llm_bench.py`
- `W3/LLM-Bench/run_gpt5_our_attack_full.py`

## Detection Methods

The repository also includes the code needed to run the DataSentinel defense under:

- `W3/Detection-Methods/run_datasentinel_prediction_results.py`
- `W3/Detection-Methods/run_datasentinel_prediction_results.sh`
- `W3/Detection-Methods/prepare_prediction_results.py`
- `W3/Detection-Methods/probe_5_samples.py`
- `W3/Detection-Methods/Detection-based/Open-Prompt-Injection/`

## Notes

- The upstream `Open-Prompt-Injection` code is included as a local dependency.
- Large model checkpoints and Hugging Face cache are not included.
- Running DataSentinel still requires a compatible base model and a downloaded fine-tuned checkpoint passed via `DATASENTINEL_FT_PATH`.
