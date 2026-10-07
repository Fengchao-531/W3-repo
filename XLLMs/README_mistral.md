# W3 Ministral 8B rerun

Model: `mistralai/Ministral-8B-Instruct-2410`.

Output: `XLLMs/Mistral`.

```bash
bash XLLMs/run_mistral_experiments.sh exp1
bash XLLMs/run_mistral_experiments.sh exp3
```

`all` runs Exp1 core first and Exp3 second. Exp2 Task Binding and Safety H1/H2/H3
are excluded. Existing completed runs are skipped unless `--force` is supplied.
