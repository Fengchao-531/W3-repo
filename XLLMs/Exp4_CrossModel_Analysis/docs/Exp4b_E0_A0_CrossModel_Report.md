# Exp4b E0 vs A0 Cross-Model Summary

Exp4b compares E0 (external artifact observation, no general preference, no binding) against A0 (user-context artifact mention only, no general preference, no binding). Positive deltas mean higher artifact action in A0 than E0.

## Artifact-Action Paired Effects

| model | E0_rate | A0_rate | A0_minus_E0 | ci_low | ci_high | mcnemar_exact_p |
| --- | --- | --- | --- | --- | --- | --- |
| Llama3.1 | 0 | 0.6 | 0.6 | 0.5278 | 0.6722 | 6.163e-33 |
| Qwen | 0 | 0.3333 | 0.3333 | 0.2667 | 0.4 | 1.735e-18 |
| Gemma | 0 | 0 | 0 | 0 | 0 |  |
| Mistral | 0.03333 | 0.2056 | 0.1722 | 0.1222 | 0.2278 | 9.313e-10 |
| DeepSeek | 0 | 0 | 0 | 0 | 0 |  |

## Macro Summary

| metric | comparison | n_models | macro_mean_delta_A0_minus_E0 | model_min_delta | model_max_delta | bootstrap_ci_low_across_models | bootstrap_ci_high_across_models |
| --- | --- | --- | --- | --- | --- | --- | --- |
| malicious_selected | E0_vs_A0 | 5 | 0.2211 | 0 | 0.6 | 0.03444 | 0.4267 |
| artifact_action | E0_vs_A0 | 5 | 0.2211 | 0 | 0.6 | 0.03444 | 0.4267 |
| attack_success_human | E0_vs_A0 | 5 | 0.2211 | 0 | 0.6 | 0.03444 | 0.4267 |
| legitimate_utility | E0_vs_A0 | 5 | -0.03111 | -0.07222 | 0 | -0.05556 | -0.008889 |

## Reading

- The cross-model mean A0-E0 artifact-action delta is 0.221.
- Llama3.1, Qwen, and Mistral show a clear A0 > E0 gap; Gemma and DeepSeek are floor cases for artifact action under these conditions.
- This supports the interpretation that the Exp4 effect is not reducible to explicit user preference: source/location still matters after removing general preference and binding.
