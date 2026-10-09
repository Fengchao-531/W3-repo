# RQ3 upstream defenses and AgentDojo adapters

This replaces the old system-prompt policy table. No defense silently falls back to a made-up system prompt. Original repositories and checkpoint weights are installed separately.

## Source and mechanism

| Defense | Source code | AgentDojo integration |
| --- | --- | --- |
| Sandwich | https://github.com/facebookresearch/SecAlign/blob/main/test.py | Author's trailing task reminder after the data (this method is inherently a prompting baseline). |
| StruQ | https://github.com/Sizhe-Chen/StruQ | Original structured-query format and separately trained model checkpoint. |
| SecAlign | https://github.com/facebookresearch/SecAlign | Original structured-query format and preference-optimized full checkpoint or LoRA. |
| Perplexity | https://github.com/neelsjain/baseline-defenses/blob/main/perplexity_filter.py | Imports original PerplexityFilter and screens untrusted observations and user-relayed offer text. |
| DataSentinel | https://github.com/liu00222/Open-Prompt-Injection | Imports original DataSentinelDetector and loads its fine-tuned checkpoint; screens untrusted observations. |
| CausalArmor | https://github.com/prashantkul/causal-armor | Uses an independent third-party implementation of the paper (NOT verified as the authors' own code), guards proposed FunctionCalls before tool execution, does LOO, sanitization and regeneration. |

CausalArmor paper: https://arxiv.org/abs/2602.07918

## Install

Install the project's optional agent dependencies, then clone the authors' repositories in a separately managed environment. Respect the upstream licenses and requirements. Examples:

    pip install -e '.[agent,internal,test]'
    git clone https://github.com/Sizhe-Chen/StruQ external/StruQ
    git clone https://github.com/facebookresearch/SecAlign external/SecAlign
    git clone https://github.com/neelsjain/baseline-defenses external/baseline-defenses
    git clone https://github.com/liu00222/Open-Prompt-Injection external/Open-Prompt-Injection
    pip install 'causal-armor[openai]'

Required environment variables:

- StruQ: W3_STRUQ_REPO, W3_STRUQ_MODEL; optional W3_STRUQ_LORA and W3_STRUQ_FORMAT (defaults to SpclSpclSpcl).
- SecAlign: W3_SECALIGN_REPO, W3_SECALIGN_MODEL; optional W3_SECALIGN_LORA and W3_SECALIGN_FORMAT. IMPORTANT: use a *defensively tuned* checkpoint/adapter, never an untrained base model alone.
- Perplexity: W3_PERPLEXITY_REPO, W3_PERPLEXITY_MODEL, W3_PERPLEXITY_THRESHOLD, optional W3_PERPLEXITY_WINDOW. The upstream implementation requires CUDA. The current adapter uses its full-text filter(), not filter_window(); calibrate threshold independently.
- DataSentinel: W3_DATASENTINEL_REPO, W3_DATASENTINEL_CONFIG, W3_DATASENTINEL_CHECKPOINT. Obtain the actual tuned detector checkpoint from the authors.
- CausalArmor: W3_CAUSAL_ACTION_MODEL, W3_CAUSAL_PROXY_URL (live vLLM proxy), W3_CAUSAL_SANITIZER_MODEL; optional W3_CAUSAL_MARGIN_TAU. Configure API credentials and providers following the third-party project's documentation.

## Run

    source-relocation build --domain travel --manifest outputs/manifests/travel.jsonl
    source-relocation run --rq rq3 --experiment defenses --model gpt4o --domain travel --defense datasentinel
    source-relocation analyze

The --defense flag allows one defense name, none or all. Running all requires all applicable checkpoints, GPU resources and providers. Preview mode prints configurations without running the agents.

## Critical scientific limitations

1. Training-based StruQ/SecAlign *replace the model*. Their scores are NOT treatment effects for an unchanged GPT-4o/Claude/Gemini. Use architecture-matched undefended controls, report the actual checkpoints, and validate tool-use formatting.
2. Sandwich uses a prompt by design; it should not be misrepresented as a learned detector.
3. The CausalArmor independent implementation operates on untrusted *tool result* spans. It does not automatically recognize relayed user-context text as a separate low-trust span.
4. The new implementation has not reproduced or verified any values in the paper. Do not attribute the manuscript's Table 3 or Figure 9 to these new adapters until actual jobs finish and outputs are audited.
5. Controlled apply_offer is an executed registered *simulated offer action*, not a browser visit to a live attacker URL.
6. The repository's pre-existing Claude/Gemini routing still needs dedicated provider clients. An OpenAI SDK client does not automatically access those providers.

## Hook order

SystemMessage -> InitQuery -> InputDefense -> LLM -> [ActionDefense -> ToolsExecutor -> InputDefense -> LLM] (loop)

Every run retains trajectories and now records defense_events, defense_impl and actual_model_id. Missing setup raises a configuration error rather than silently running an ineffective defense.
