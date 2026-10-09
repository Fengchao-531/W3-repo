# Installation

Use Python 3.11 with the AgentDojo v1.2.2 suite and OpenAI function-calling support. Model execution requires the corresponding provider credentials or local Hugging Face checkpoint.

```bash
conda env create -f environment.yml
conda activate source-relocation
pip install -e '.[agent,internal,test]'
```

For GPT-4o, set `OPENAI_API_KEY` in the running environment. For open-weight models, configure the Hugging Face cache and GPU placement through Transformers environment variables.

All generated manifests, trajectories, activation measurements, statistics, figures, and tables are written inside `outputs/`.
