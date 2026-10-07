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
| CausalArmor | BM | 0.027777777777777776 | 0.23333333333333334 | 0.20555555555555555 |
| CausalArmor | M | 0.016666666666666666 | 0.40555555555555556 | 0.3888888888888889 |
| DataSentinel-D | BM | 0.022222222222222223 | 0.23333333333333334 | 0.2111111111111111 |
| DataSentinel-D | M | 0.011111111111111112 | 0.39444444444444443 | 0.3833333333333333 |
| SecAlign | BM | 0.016666666666666666 | 0.22777777777777777 | 0.2111111111111111 |
| SecAlign | M | 0.022222222222222223 | 0.4166666666666667 | 0.3944444444444445 |
| StruQ | BM | 0.03333333333333333 | 0.18333333333333332 | 0.15 |
| StruQ | M | 0.03333333333333333 | 0.36666666666666664 | 0.3333333333333333 |
