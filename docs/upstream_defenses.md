# RQ3 Defense Integration

The defense runner supports the six methods used in RQ3 through dedicated AgentDojo integration stages.

## Methods and source code

| Method | Source | Interface |
| --- | --- | --- |
| Sandwich | [SecAlign test.py](https://github.com/facebookresearch/SecAlign/blob/main/test.py) | Appends the task reminder after task-related external content |
| StruQ | [StruQ](https://github.com/Sizhe-Chen/StruQ) | Loads the trained checkpoint and structured-query format |
| SecAlign | [SecAlign](https://github.com/facebookresearch/SecAlign) | Loads the trained checkpoint or LoRA and structured-query format |
| Perplexity | [PerplexityFilter](https://github.com/neelsjain/baseline-defenses/blob/main/perplexity_filter.py) | Runs the scoring filter on artifact spans and tool observations |
| DataSentinel | [Open-Prompt-Injection](https://github.com/liu00222/Open-Prompt-Injection) | Runs DataSentinelDetector on artifact spans and tool observations |
| CausalArmor | [CausalArmor implementation](https://github.com/prashantkul/causal-armor) | Guards proposed tool actions with attribution and action regeneration |

## Installation

```bash
pip install -e '.[agent,internal,test]'
git clone https://github.com/Sizhe-Chen/StruQ.git external/StruQ
git clone https://github.com/facebookresearch/SecAlign.git external/SecAlign
git clone https://github.com/neelsjain/baseline-defenses.git external/baseline-defenses
git clone https://github.com/liu00222/Open-Prompt-Injection.git external/Open-Prompt-Injection
pip install 'causal-armor[openai]'
```

Install each referenced project's Python dependencies and obtain the corresponding checkpoints.

## Configuration

| Method | Environment variables |
| --- | --- |
| StruQ | `W3_STRUQ_REPO`, `W3_STRUQ_MODEL`, optional `W3_STRUQ_LORA`, `W3_STRUQ_FORMAT` |
| SecAlign | `W3_SECALIGN_REPO`, `W3_SECALIGN_MODEL`, optional `W3_SECALIGN_LORA`, `W3_SECALIGN_FORMAT` |
| Perplexity | `W3_PERPLEXITY_REPO`, `W3_PERPLEXITY_MODEL`, `W3_PERPLEXITY_THRESHOLD`, optional `W3_PERPLEXITY_WINDOW` |
| DataSentinel | `W3_DATASENTINEL_REPO`, `W3_DATASENTINEL_CONFIG`, `W3_DATASENTINEL_CHECKPOINT` |
| CausalArmor | `W3_CAUSAL_ACTION_MODEL`, `W3_CAUSAL_PROXY_URL`, `W3_CAUSAL_SANITIZER_MODEL`, optional `W3_CAUSAL_MARGIN_TAU` |

The selected checkpoints, provider configuration, and filter thresholds are set through the corresponding method variables.

## Execution

```bash
source-relocation build --domain travel --manifest outputs/manifests/travel.jsonl
source-relocation run --rq rq3 --experiment defenses --model gpt4o --domain travel --defense datasentinel
source-relocation analyze
```

Use `--defense` to select `none`, `sandwich`, `struq`, `secalign`, `perplexity`, `datasentinel`, `causalarmor`, or `all`.

The defense stages follow:

```text
SystemMessage -> InitQuery -> InputDefense -> LLM
                                      |
                           ActionDefense -> ToolsExecutor
                                      |
                                 InputDefense -> LLM
```

Result records include `defense_events`, `defense_impl`, `actual_model_id`, `task_success`, `malicious_action_executed`, and `safe_completion`.
