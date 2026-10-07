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
| CausalArmor | BM | 0.022222222222222223 | 0.16111111111111112 | 0.1388888888888889 |
| CausalArmor | M | 0.011111111111111112 | 0.2 | 0.1888888888888889 |
| DataSentinel-D | BM | 0.044444444444444446 | 0.12777777777777777 | 0.08333333333333331 |
| DataSentinel-D | M | 0.027777777777777776 | 0.1388888888888889 | 0.11111111111111112 |
| SecAlign | BM | 0.011111111111111112 | 0.011111111111111112 | 0.0 |
| SecAlign | M | 0.005555555555555556 | 0.027777777777777776 | 0.02222222222222222 |
| StruQ | BM | 0.027777777777777776 | 0.11666666666666667 | 0.08888888888888889 |
| StruQ | M | 0.022222222222222223 | 0.07777777777777778 | 0.05555555555555555 |
