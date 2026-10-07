# W3 multi-model launcher

Runs are sequential so one GPU is reused safely. With no model list, Llama,
Mistral, and DeepSeek run immediately; Qwen, Gemma, and OLMo are included when
their model-path variables are set.

```bash
# One experiment across every available model
bash run_all_models.sh exp1
bash run_all_models.sh exp3

# Both experiments across every available model
bash run_all_models.sh all

# Selected models only
bash run_all_models.sh exp1 llama mistral deepseek
bash run_all_models.sh exp3 gemma olmo

# Forward runner options after --
bash run_all_models.sh exp1 llama gemma -- --limit 4
```

Optional checkpoint locations:

```bash
export QWEN_MODEL_PATH=/path/to/qwen-instruct/snapshot
export GEMMA_MODEL_PATH=/path/to/gemma-instruct/snapshot
export OLMO_MODEL_PATH=/path/to/olmo-instruct/snapshot
```

An explicitly selected model fails when its path variable is absent. During a
default all-model run, models with missing path variables are reported and
skipped. Set `STRICT_MODELS=1` to make missing optional models fail that run.
