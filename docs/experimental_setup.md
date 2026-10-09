# Experimental Framework

The controlled environment uses AgentDojo v1.2.2 with Travel, Workspace, Banking, and Slack tasks. Each Travel source condition uses 20 base tasks, 3 benefit dimensions, and 3 carrier variants, producing 180 matched task-artifact configurations. The dimensions are resource saving, quality/reliability, and convenience/experience. Carrier types are promotion, tip, and resource.

Each task has a malicious artifact M, a benefit-matched benign artifact BM, and an alternative benign artifact BW. M and BM retain the same visible code and claimed benefit while pointing to different destinations. In the Travel examples, M uses `https://lemarais-offers.example/book` and BM uses `https://lemarais.example/book`. The external candidates and their order stay fixed within each matched comparison.

Request components are R for the original task, D for an artifact description, P for a general preference, I for an explicit artifact-use instruction, and V for conflicting reliability evidence. The operator + indicates component inclusion rather than mandatory sentence order.

RQ1 Exp1 compares E: R, UC_M: R+D_M, and UC_BM: R+D_BM without P or I. Exp2 places the same D_M or D_BM at the beginning, middle, or end of the initial task request. Exp3 compares R+D and R+P+D for each artifact type. Exp4 compares R+P+D_M and R+P+D_M+I using separate paired runs. Exp5 introduces V under the external and user-context source conditions. The source-label control changes only the textual attribution `Source: external` versus `Source: user-provided` while keeping candidate content, message role, and presentation fixed.

The controlled model set is GPT-4o, Claude 3.5, Gemini 2.5, Llama 3.1, Qwen 2.5, Gemma 2, Ministral-8B, and DeepSeek-R1. The original GPT-4o Travel configuration uses `gpt-4o-2024-05-13`, temperature 0, tool iteration limit 10, and no separate planning module. Runs reset the task environment and offer state before execution.
