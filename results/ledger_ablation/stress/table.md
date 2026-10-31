Regime **stress**, seeds [38, 39, 40, 41, 42]. p-values vs L1_full.

| Config | Success % | URLLC on-time % | Rejected % | Late % | Lp95 exec (s) | Cloud % | LI % | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|
| L1_full | 75.89 ± 1.26 | 40.02 ± 4.41 | 22.89 ± 1.13 | 1.22 ± 0.14 | 29.47 ± 0.78 | 22.31 ± 0.79 | 75.50 ± 0.83 | ref | ref |
| L2_noquar_eval | 75.93 ± 1.26 | 40.13 ± 4.35 | 22.82 ± 1.15 | 1.24 ± 0.18 | 29.31 ± 0.98 | 22.35 ± 0.73 | 75.43 ± 0.77 | 1.000 | 0.66 |
| L3_noquar_trained | 75.80 ± 1.10 | 39.43 ± 2.98 | 22.90 ± 0.96 | 1.30 ± 0.21 | 28.89 ± 0.48 | 23.44 ± 0.75 | 74.26 ± 0.82 | 0.750 | 0.76 |
| L4_noshape | 75.58 ± 1.03 | 39.41 ± 2.49 | 23.18 ± 1.00 | 1.24 ± 0.13 | 28.38 ± 1.54 | 20.77 ± 0.61 | 76.69 ± 0.58 | 0.250 | 0.33 |
| L5_ledger_off | 77.68 ± 0.98 | 40.44 ± 2.67 | 21.13 ± 0.96 | 1.19 ± 0.08 | 27.08 ± 0.37 | 17.62 ± 0.59 | 80.57 ± 0.66 | 0.062 | 6.3e-09 |
| L1_full_seed2 | 76.87 ± 0.66 | 41.83 ± 2.56 | 22.07 ± 0.79 | 1.06 ± 0.13 | 30.92 ± 1.57 | 29.94 ± 0.43 | 67.96 ± 0.46 | 0.062 | 0.00096 |
| L5_ledger_off_seed2 | 76.08 ± 1.15 | 31.61 ± 4.04 | 22.96 ± 1.15 | 0.96 ± 0.11 | 32.93 ± 1.85 | 18.06 ± 0.47 | 79.71 ± 0.64 | 0.438 | 0.54 |
| L6_offmodel_ledger_on | 77.70 ± 0.91 | 40.41 ± 2.83 | 21.13 ± 0.90 | 1.17 ± 0.12 | 27.08 ± 0.35 | 17.69 ± 0.68 | 80.45 ± 0.77 | 0.062 | 4.3e-09 |

Quarantine counts (pooled over seeds):

- L1_full: {'urllc_tasks': 3667, 'urllc_with_quarantined_server': 671, 'urllc_rejected_while_some_server_quarantined': 443}
- L2_noquar_eval: {'urllc_tasks': 3667, 'urllc_with_quarantined_server': 0, 'urllc_rejected_while_some_server_quarantined': 0}
- L3_noquar_trained: {'urllc_tasks': 3667, 'urllc_with_quarantined_server': 0, 'urllc_rejected_while_some_server_quarantined': 0}
- L4_noshape: {'urllc_tasks': 3667, 'urllc_with_quarantined_server': 588, 'urllc_rejected_while_some_server_quarantined': 413}
- L5_ledger_off: {'urllc_tasks': 3667, 'urllc_with_quarantined_server': 0, 'urllc_rejected_while_some_server_quarantined': 0}
- L1_full_seed2: {'urllc_tasks': 3667, 'urllc_with_quarantined_server': 98, 'urllc_rejected_while_some_server_quarantined': 69}
- L5_ledger_off_seed2: {'urllc_tasks': 3667, 'urllc_with_quarantined_server': 0, 'urllc_rejected_while_some_server_quarantined': 0}
- L6_offmodel_ledger_on: {'urllc_tasks': 3667, 'urllc_with_quarantined_server': 283, 'urllc_rejected_while_some_server_quarantined': 209}
