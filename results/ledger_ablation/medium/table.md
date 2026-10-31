Regime **medium**, seeds [38, 39, 40, 41, 42]. p-values vs L1_full.

| Config | Success % | URLLC on-time % | Rejected % | Late % | Lp95 exec (s) | Cloud % | LI % | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|
| L1_full | 99.48 ± 0.21 | 97.39 ± 1.00 | 0.14 ± 0.16 | 0.38 ± 0.10 | 19.29 ± 0.30 | 19.79 ± 0.61 | 80.21 ± 0.61 | ref | ref |
| L2_noquar_eval | 99.48 ± 0.21 | 97.39 ± 1.00 | 0.14 ± 0.16 | 0.38 ± 0.10 | 19.29 ± 0.30 | 19.79 ± 0.61 | 80.21 ± 0.61 | 1.000 | 1 |
| L3_noquar_trained | 99.48 ± 0.21 | 97.39 ± 1.00 | 0.14 ± 0.16 | 0.38 ± 0.10 | 19.30 ± 0.30 | 19.79 ± 0.61 | 80.21 ± 0.61 | 1.000 | 1 |
| L4_noshape | 98.93 ± 0.20 | 94.70 ± 1.03 | 0.63 ± 0.28 | 0.43 ± 0.11 | 19.30 ± 0.39 | 20.22 ± 0.47 | 79.76 ± 0.48 | 0.062 | 3.9e-07 |
| L5_ledger_off | 99.39 ± 0.15 | 98.59 ± 0.37 | 0.06 ± 0.06 | 0.55 ± 0.17 | 19.54 ± 0.34 | 14.20 ± 1.81 | 85.27 ± 1.89 | 0.562 | 0.4 |

Quarantine counts (pooled over seeds):

- L1_full: {'urllc_tasks': 2404, 'urllc_with_quarantined_server': 0, 'urllc_rejected_while_some_server_quarantined': 0}
- L2_noquar_eval: {'urllc_tasks': 2404, 'urllc_with_quarantined_server': 0, 'urllc_rejected_while_some_server_quarantined': 0}
- L3_noquar_trained: {'urllc_tasks': 2404, 'urllc_with_quarantined_server': 0, 'urllc_rejected_while_some_server_quarantined': 0}
- L4_noshape: {'urllc_tasks': 2404, 'urllc_with_quarantined_server': 6, 'urllc_rejected_while_some_server_quarantined': 0}
- L5_ledger_off: {'urllc_tasks': 2404, 'urllc_with_quarantined_server': 0, 'urllc_rejected_while_some_server_quarantined': 0}
