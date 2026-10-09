# Quick Start

Build the task-artifact configurations directly from AgentDojo:

```bash
source-relocation build --domain travel --manifest outputs/manifests/travel.jsonl
```

Run the three source-relocation conditions with GPT-4o:

```bash
source-relocation run --rq rq1 --experiment relocation --model gpt4o --domain travel
```

Run the user-context position comparison:

```bash
source-relocation run --rq rq1 --experiment position --model gpt4o --domain travel
```

Run the preference, explicit-use, source-label, and reliability comparisons:

```bash
source-relocation run --rq rq1 --experiment preference --model gpt4o
source-relocation run --rq rq1 --experiment instruction --model gpt4o
source-relocation run --rq rq1 --experiment source_label --model gpt4o
source-relocation run --rq rq1 --experiment reliability --model gpt4o
```

Compute result tables and plot the behavioral comparisons:

```bash
source-relocation analyze
python plotting/rq1_figures.py --summary outputs/analysis/summary.csv --out outputs/figures/rq1.pdf
```

Run the verification and defense comparisons:

```bash
source-relocation run --rq rq3 --experiment verification --model gpt4o
source-relocation run --rq rq3 --experiment defenses --model gpt4o
```
