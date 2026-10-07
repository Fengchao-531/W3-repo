# RQ3 Defense Table Fill

## Can This Table Be Filled?

Yes, but only partially and with a clearly stated scope.

The four defense rows can be filled from completed RQ3-B matched reruns for the four complete XLLM models:

- Gemma
- Llama3.1
- Mistral
- Qwen

DeepSeek RQ3-B is incomplete and excluded. GPT-4o RQ3-B has no processed matched rerun table and is excluded.

The no-defense row can be filled only as a reference baseline from Exp1/RQ3-A no-defense data, not from an explicit RQ3-B `E_BM` no-defense matched condition. Therefore, label it as "no-defense reference baseline", not as a fully matched RQ3-B baseline.

## Metric Definition Used Here

- Task success rate: `benign_task_success` for RQ3-B defense runs; `utility_success` for Exp1 no-defense baseline.
- Safety completion rate: `security_success` on malicious-artifact runs, equivalent to `1 - attack_success`.
- Aggregation: pooled over completed XLLM models, weighted by run count.
- Defense rows: task success uses both M and BM rows under the same source; safety uses M rows only.
- No-defense row: task success uses Exp1 E runs and Exp1 UC_M + UC_B runs; safety uses Exp1 E and Exp1 UC_M malicious-risk runs.

## Filled Table

| Model / Prompt | E: Task Success ↑ | UC: Task Success ↑ | E: Safety Completion ↑ | UC: Safety Completion ↑ |
|---|---:|---:|---:|---:|
| No-defense reference baseline | 65/720 (9.0%) | 117/1440 (8.1%) | 659/720 (91.5%) | 459/720 (63.8%) |
| Source-instruction separation / StruQ | 72/1440 (5.0%) | 93/1440 (6.5%) | 654/720 (90.8%) | 489/720 (67.9%) |
| Task and safety constraints / SecAlign | 106/1440 (7.4%) | 93/1440 (6.5%) | 657/720 (91.2%) | 473/720 (65.7%) |
| Malicious-content checking / DataSentinel-D | 108/1440 (7.5%) | 100/1440 (6.9%) | 657/720 (91.2%) | 469/720 (65.1%) |
| Action-necessity checking / CausalArmor | 122/1440 (8.5%) | 107/1440 (7.4%) | 647/720 (89.9%) | 453/720 (62.9%) |

## Chinese Table Version

| 模型／提示 | E：任务成功率 ↑ | UC：任务成功率 ↑ | E：安全完成率 ↑ | UC：安全完成率 ↑ |
|---|---:|---:|---:|---:|
| 无防御参考基线 | 65/720 (9.0%) | 117/1440 (8.1%) | 659/720 (91.5%) | 459/720 (63.8%) |
| 来源与指令区分 | 72/1440 (5.0%) | 93/1440 (6.5%) | 654/720 (90.8%) | 489/720 (67.9%) |
| 任务与安全约束 | 106/1440 (7.4%) | 93/1440 (6.5%) | 657/720 (91.2%) | 473/720 (65.7%) |
| 恶意内容检查 | 108/1440 (7.5%) | 100/1440 (6.9%) | 657/720 (91.2%) | 469/720 (65.1%) |
| 行动必要性检查 | 122/1440 (8.5%) | 107/1440 (7.4%) | 647/720 (89.9%) | 453/720 (62.9%) |

## Interpretation Notes

1. The defense names are adapted prompt-based implementations, not original StruQ/SecAlign/DataSentinel-D/CausalArmor detector or checkpoint implementations.
2. The strongest UC safety completion rate among these prompt defenses is StruQ: 67.9%, compared with the no-defense reference baseline of 63.8%.
3. E safety completion is already high in the no-defense baseline, so defense rows do not show a clear improvement under E.
4. Task success rates are low for these local models overall; safety improvements should be interpreted together with this low utility.
5. This table should not include DeepSeek or GPT-4o unless their RQ3-B processed matched reruns are completed/recovered.
