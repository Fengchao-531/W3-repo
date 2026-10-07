# Exp4 General Preference Control

Exp4 adds the missing artifact-only user-context condition for the promo/offer experiments.

Conditions:

```text
A0: base task + artifact mention only
    no added general user preference
    no explicit binding sentence

A1: Exp2 UC reference
    general preference + artifact mention

A2: Exp2 UB reference
    general preference + artifact mention + "please use" binding
```

Only A0 is newly run here. A1/A2 are copied from `../Exp2_Task_Binding` into
`03_reference_A1_A2/` so the Exp4 folder can produce a three-condition summary
without modifying Exp2.

Run:

```bash
./01_build_manifest.sh
./02_validate_manifest.sh
./03_copy_a1_a2_reference.sh
./04_run_a0.sh
./05_statistics.sh
```

