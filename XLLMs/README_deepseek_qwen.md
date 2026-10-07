# DeepSeek and Qwen W3 reruns

DeepSeek uses the installed `DeepSeek-R1-Distill-Qwen-7B` snapshot and writes to
`XLLMs/DeepSeek`.

```bash
bash XLLMs/run_deepseek_experiments.sh exp1
bash XLLMs/run_deepseek_experiments.sh exp3
```

No standalone Qwen snapshot is currently installed. Set `QWEN_MODEL_PATH` to a
local Qwen Instruct snapshot; results write to `XLLMs/Qwen`.

```bash
export QWEN_MODEL_PATH=/absolute/path/to/qwen/snapshot
bash XLLMs/run_qwen_experiments.sh exp1
bash XLLMs/run_qwen_experiments.sh exp3
```
