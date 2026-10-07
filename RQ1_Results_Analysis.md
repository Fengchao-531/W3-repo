# RQ1 Results Analysis

This note summarizes the behavioral evidence for RQ1 from the W3 experiments:

- Exp1: `Exp1_User_Context_Embedding`
- Exp2: `Exp2_Task_Binding`

The core RQ1 thread is:

> When relevant artifact information moves from the external environment into the user context, does the agent's downstream behavior change?

Exp1 establishes the main behavioral phenomenon. Exp2 checks whether the high adoption observed under user-context embedding depends on an additional explicit binding sentence. The wording below is intentionally conservative: `M` is the malicious-designated candidate in the experiment, and the measured outcome is whether the agent selected or acted on that registered candidate. These results should not be read as direct evidence of credential theft, malware execution, or other real-world downstream harms beyond the operationalized behavior in the benchmark.

## What RQ1 Answers

| Question | Current answer | Evidence and boundary |
| --- | --- | --- |
| Does placing a candidate artifact in user context change final adoption? | Yes, substantially in this setting | `M`: 27.8% in `E` to 95.6% in `UC_M`; this is the effect of the full user-context embedding condition |
| Is the effect unique to malicious candidates? | No | `BM`: 13.9% in `E` to 86.7% in `UC_B`; benign matched candidates show the same broad pattern |
| Is explicit "please use this" binding necessary for high adoption? | No evidence that it is necessary | Exp2 `UC` already reaches 89.4% `M` adoption |
| Does explicit binding add further adoption? | Point estimate increases, but evidence is not decisive | `UC` to `UB`: +5.0 pp; McNemar `p = 0.093`; cluster bootstrap CI crosses zero |
| Does this prove the agent trusts the user source more? | Not by Exp1/Exp2 alone | Exp1 changes source, timing, visibility, position, and salience together |
| Does adoption necessarily mean original-task failure? | No | Many `M` adoptions co-occur with utility success |

The best current RQ1 claim is therefore: user-context embedding is associated with a large shift in artifact adoption, and this shift does not require an extra explicit task-binding sentence. A stronger source-provenance claim requires the controlled source experiment that holds content, timing, position, candidate set, and exposure fixed.

## Shared Setting

| Item | Setting |
| --- | --- |
| Benchmark | AgentDojo Travel v1 |
| Base tasks | 20 original user tasks |
| Desire variants | saving, quality, experience |
| Carrier variants | promotion, tip, resource |
| Matched instances | 180 |
| Model | `gpt-4o-2024-05-13` |
| Temperature | 0.0 |
| Candidate set | `M`, `BM`, `BW` |
| Main behavioral outcome | final selected/applied candidate: `M`, `BM`, `BW`, or `None` |

`BM` is benefit-matched to `M`, so the benign-control comparison is central. It tests whether the behavior is specific to the malicious-designated artifact or whether user-context embedding more generally privileges the embedded artifact.

## Exp1: User-Context Embedding

Exp1 compares three behavioral conditions:

| Condition | Description | Embedded artifact |
| --- | --- | --- |
| `E` | Candidates are available only through external/tool retrieval | none |
| `UC_M` | `M` additionally appears in the initial user context | `M` |
| `UC_B` | benefit-matched benign candidate additionally appears in the initial user context | `BM` |

### Overall Choices

| Condition | M selected | BM selected | BW selected | None | Utility |
| --- | ---: | ---: | ---: | ---: | ---: |
| `E` | 50/180 = 27.8% | 25/180 = 13.9% | 0/180 = 0.0% | 105/180 = 58.3% | 70.0% |
| `UC_M` | 172/180 = 95.6% | 0/180 = 0.0% | 0/180 = 0.0% | 8/180 = 4.4% | 73.3% |
| `UC_B` | 4/180 = 2.2% | 156/180 = 86.7% | 0/180 = 0.0% | 20/180 = 11.1% | 72.8% |

The main effect is large. When `M` appears in user context, its adoption rises from 27.8% to 95.6%, a +67.8 percentage-point lift. When `BM` appears in user context, its adoption rises from 13.9% to 86.7%, a +72.8 percentage-point lift. The `UC_B` condition also sharply suppresses `M` adoption, from 27.8% in `E` to 2.2% in `UC_B`.

This supports a context-embedding effect on artifact adoption. It does not yet isolate source/provenance, because moving an artifact from `E` to `UC` also changes timing, initial visibility, salience, context position, and possible repetition.

### Paired Target Tests

| Paired comparison | Target outcome | Toward target | Away from target | Test result |
| --- | --- | ---: | ---: | --- |
| `E -> UC_M` | `M` selected | 125 | 3 | McNemar `p = 2.05e-33` |
| `E -> UC_B` | `BM` selected | 135 | 4 | McNemar `p = 4.40e-35` |

Because the 180 rows are derived from 20 base tasks, pair-level McNemar tests should be paired with base-task-aware summaries. A simple base-task cluster bootstrap still gives large positive effects:

| Effect | Task-level mean lift | 95% task-cluster bootstrap CI | Positive base tasks |
| --- | ---: | ---: | ---: |
| `UC_M - E` on `M` uptake | +67.8 pp | [57.2 pp, 77.2 pp] | 20/20 |
| `UC_B - E` on `BM` uptake | +72.8 pp | [66.1 pp, 79.4 pp] | 20/20 |

### Choice Migration

The full migration matters because the effect is not merely "more artifact use"; it changes which candidate wins.

#### `E -> UC_M`

| `E` choice | `UC_M = M` | `UC_M = None` |
| --- | ---: | ---: |
| `M` | 47 | 3 |
| `BM` | 25 | 0 |
| `None` | 100 | 5 |

Most of the `UC_M` lift comes from `None` and `BM` cases moving to `M`. Only three instances move away from `M` after malicious embedding.

#### `E -> UC_B`

| `E` choice | `UC_B = BM` | `UC_B = M` | `UC_B = None` |
| --- | ---: | ---: | ---: |
| `M` | 44 | 0 | 6 |
| `BM` | 21 | 0 | 4 |
| `None` | 91 | 4 | 10 |

Benign embedding redirects many previously malicious or null selections toward the benefit-matched benign candidate. This is the clearest evidence that the phenomenon is broader than malicious-candidate uptake.

### Exp1 Interpretation

Exp1 provides strong behavioral evidence that putting an artifact into user context changes which artifact the agent eventually applies. The benign-control result is essential: it shows that maliciousness is not necessary for the context-embedding effect.

The result should not be overread as proof that the agent trusts malicious content because it is malicious, or that a source label alone caused the shift. Exp1 establishes a context-placement/adoption association under the implemented conditions.

## Exp2: Task Binding

Exp2 re-runs the frozen Exp1 `UC_M` instance set with two conditions:

| Condition | Description |
| --- | --- |
| `UC` | `M` appears in user context, without an additional explicit use instruction |
| `UB` | `UC` plus a carrier-specific binding sentence such as "Please use this offer if applicable" |

The purpose is to test whether high adoption requires explicit task-binding language.

### Primary Results

| Metric | `UC` | `UB` | Difference |
| --- | ---: | ---: | ---: |
| `P(M)` | 161/180 = 89.4% | 170/180 = 94.4% | +5.0 pp |
| Artifact action rate | 89.4% | 94.4% | +5.0 pp |
| Registered `M` action-success flag | 89.4% | 94.4% | +5.0 pp |
| Utility | 76.1% | 70.6% | -5.6 pp |

The point estimate is positive, but the baseline `UC` rate is already very high. Thus, Exp2 mainly supports the claim that explicit binding is not necessary for high adoption.

The three headline behavioral metrics in Exp2 are numerically identical. Unless the annotation code demonstrates that they are distinct events, they should not be presented as three independent pieces of evidence.

### Paired Transitions

| `UC` choice | `UB = M` | `UB = None` |
| --- | ---: | ---: |
| `M` | 154 | 7 |
| `None` | 16 | 3 |

| Test / interval | Result |
| --- | ---: |
| McNemar p-value | 0.093 |
| Cluster bootstrap estimate | +5.0 pp |
| Cluster bootstrap 95% CI | [-1.1 pp, +11.7 pp] |

Exp2 therefore suggests that explicit task-binding language may add a small amount of adoption, but the evidence is not strong enough to claim a clear additional effect under conventional thresholds. The conservative conclusion is: high adoption appears without binding; binding has a positive but statistically uncertain incremental effect.

## Utility and Risk Interpretation

Artifact adoption and original-task success are not mutually exclusive. This matters because a pure utility metric can miss risk-relevant behavior.

| Condition | Adopted `M` and utility success | Adopted `M` and utility failure | Did not adopt `M` and utility success | Did not adopt `M` and utility failure |
| --- | ---: | ---: | ---: | ---: |
| Exp1 `E` | 32 | 18 | 94 | 36 |
| Exp1 `UC_M` | 128 | 44 | 4 | 4 |
| Exp1 `UC_B` | 1 | 3 | 130 | 46 |
| Exp2 `UC` | 125 | 36 | 12 | 7 |
| Exp2 `UB` | 120 | 50 | 7 | 3 |

In many runs, the agent adopts `M` while still satisfying the original utility objective. The paper should therefore avoid framing the result only as "the agent gets distracted and fails the task." A more precise framing is that original-task success does not preclude adoption of the registered target artifact.

## Quality Controls Relevant to RQ1

The Exp1 QC report records:

- candidate-order balance: `BW-M-BM`, `M-BM-BW`, and `BM-BW-M` each occur 60 times;
- no duplicate or missing pairs;
- artifact-value matching and desire compatibility checks pass;
- carrier explicit-instruction check passes;
- artifact ID leakage check passes;
- `E`, `UC_M`, and `UC_B` candidate sets are equal;
- `E`, `UC_M`, and `UC_B` random seeds are equal;
- `UC_B` manifest inheritance and benign-matched embedding checks pass.

These controls make the Exp1 behavioral comparison cleaner, especially against fixed order and candidate-set explanations. They do not eliminate the broader difference between external availability and initial user-context embedding.

## RQ1 Synthesis

| Claim | Evidence | Conservative conclusion |
| --- | --- | --- |
| User-context embedding changes artifact adoption | Exp1: `P(M)` 27.8% to 95.6%; `P(BM)` 13.9% to 86.7% | Supported for the implemented AgentDojo Travel setting |
| The phenomenon is not unique to the malicious-designated candidate | Exp1 benign control strongly shifts adoption toward `BM` | Supported |
| Explicit "please use" binding is necessary for high adoption | Exp2 `UC` already reaches 89.4% `M` adoption | Not supported |
| Explicit binding adds adoption beyond context presence | Exp2: +5.0 pp, McNemar `p = 0.093`, cluster CI crosses zero | Suggestive only |
| Source/provenance alone explains the Exp1 effect | Exp1 changes placement, timing, visibility, salience, and repetition | Not established by Exp1/Exp2 alone |
| Actual downstream harm occurred | Adoption/action-success flags are experimental operationalizations | Not established without task-specific harm analysis |

Overall, the RQ1 behavioral result is that artifacts appearing in user context are much more likely to be adopted than artifacts available only through external retrieval, and this high adoption does not require an explicit instruction to use the artifact. The safest paper phrasing is "user-context embedding changes artifact adoption behavior." Claims about isolated source attribution should be deferred to the controlled source-provenance experiment, where content, timing, position, task, candidate set, and candidate order are held fixed.
