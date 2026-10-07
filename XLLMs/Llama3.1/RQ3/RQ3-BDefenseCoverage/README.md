# RQ3-B Defense Coverage

This folder separates two things:

1. `01_matched_manifest/`: the P1 matched rerun design required for primary RQ3-B evidence.
2. `03_legacy_import/`: old W3-Backup detector verdicts imported as appendix/robustness evidence only.

Benign matched controls are included by default, so the manifest contains `E_M`, `UC_M`, `E_BM`, and `UC_BM` for each defense. Set `RQ3_DEFENSE_INCLUDE_BM=0` only for a reduced diagnostic manifest.
