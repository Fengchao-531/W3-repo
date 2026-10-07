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
| CausalArmor | BM | 0.17777777777777778 | 0.45555555555555555 | 0.2777777777777778 |
| CausalArmor | M | 0.31666666666666665 | 0.7055555555555556 | 0.38888888888888895 |
| DataSentinel-D | BM | 0.14444444444444443 | 0.5055555555555555 | 0.3611111111111111 |
| DataSentinel-D | M | 0.2388888888888889 | 0.6777777777777778 | 0.4388888888888889 |
| SecAlign | BM | 0.15555555555555556 | 0.46111111111111114 | 0.3055555555555556 |
| SecAlign | M | 0.25555555555555554 | 0.75 | 0.49444444444444446 |
| StruQ | BM | 0.14444444444444443 | 0.4388888888888889 | 0.29444444444444445 |
| StruQ | M | 0.24444444444444444 | 0.6666666666666666 | 0.42222222222222217 |
