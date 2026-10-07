# RQ3-A Controlled Verification Intervention

## Data Integrity

| Condition | N | Exposure | Mention | Plan | Action | Security | Utility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E_M_H1 | 180 | 0.417 | 0.039 | 0.289 | 0.278 | 0.722 | 0.700 |
| UC_M_H1 | 180 | 1.000 | 0.244 | 0.978 | 0.956 | 0.044 | 0.733 |
| UC_M_H2 | 180 | 1.000 | 0.439 | 0.872 | 0.839 | 0.161 | 0.772 |
| UC_M_H3 | 180 | 1.000 | 0.550 | 0.867 | 0.800 | 0.200 | 0.694 |

## Source x Verification

| Outcome | Delta H1 | Delta H3 | Diff-in-Diff | H1 OR | H3 OR |
| --- | ---: | ---: | ---: | ---: | ---: |
| artifact_used_in_plan | 0.689 | NA | NA | 96.001 | NA |
| artifact_action_executed | 0.678 | NA | NA | 52.443 | NA |
| security_success | -0.678 | NA | NA | 0.019 | NA |

## Notes

- E_M_H3 rows appear after the new RQ3 run finishes.
- Optional E_M_H2 rows appear only when `RQ3_INCLUDE_E_M_H2=1` is used.
