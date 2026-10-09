# Outcome Definitions and Statistical Analysis

Exposure is an artifact appearing in model-visible context. Mention is an agent's reference to the artifact in generated text. Planning is an artifact incorporated in a stated downstream plan. Action execution is confirmed by an accepted and executed registered tool operation. These measures are not assumed to form a strict sequential funnel.

Artifact adoption counts a task-specific selected candidate. Malicious-action execution additionally requires an attacker-targeted operation carried out by the environment. Task utility is the AgentDojo task-success judgment, and safe completion is the intersection of successful task completion and no executed malicious action.

The principal behavioral contrast is the UC-minus-E difference in the outcome rate. GPT-4o Travel uncertainty estimates use a percentile bootstrap across 20 base-task clusters with 2,000 resamples and seed 1234. The paired observations within each sampled task are retained.

The RQ2 internal score is the mean log-probability of the teacher-forced artifact tokens. Late-layer summaries use relative decoder depth of at least 0.875. The internal intervention subset is defined by matched checkpoints. A patching intervention effect changes the internal score, not the natural agent action rate.

RQ3 reports malicious-action rate, benign artifact use, task utility, and safe completion separately. Deployed-agent evaluation uses three environmental constraints E1–E3 and three commonsense constraints C1–C3. Each category averages the three applicable constraint violation rates. Each agent is evaluated by H1, H2, and H3 and averaged across three rounds.
