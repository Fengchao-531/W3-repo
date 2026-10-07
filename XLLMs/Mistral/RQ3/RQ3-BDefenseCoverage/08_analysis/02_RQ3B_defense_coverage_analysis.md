# RQ3-B Existing Defense Coverage

## Status

- Matched primary rerun manifest is generated under `01_matched_manifest/`.
- Legacy W3-Backup detector verdicts are imported under `03_legacy_import/`.
- Legacy rows are appendix evidence only because source, position, and ordering are not isolated.

## Matched Conditions

- E_M + defense
- UC_M + defense
- E_BM + defense
- UC_BM + defense

## Defenses

- StruQ
- SecAlign
- DataSentinel-D
- CausalArmor

## Source Gaps

| Defense | Artifact | E | UC | Delta |
| --- | --- | ---: | ---: | ---: |
| CausalArmor | BM | 0.06111111111111111 | 0.12222222222222222 | 0.06111111111111111 |
| CausalArmor | M | 0.06111111111111111 | 0.17222222222222222 | 0.1111111111111111 |
| DataSentinel-D | BM | 0.06111111111111111 | 0.13333333333333333 | 0.07222222222222222 |
| DataSentinel-D | M | 0.07222222222222222 | 0.18333333333333332 | 0.1111111111111111 |
| SecAlign | BM | 0.06111111111111111 | 0.12777777777777777 | 0.06666666666666665 |
| SecAlign | M | 0.06666666666666667 | 0.17777777777777778 | 0.11111111111111112 |
| StruQ | BM | 0.06111111111111111 | 0.13333333333333333 | 0.07222222222222222 |
| StruQ | M | 0.06666666666666667 | 0.17222222222222222 | 0.10555555555555556 |
