# M14 consensus extension: regime stress

Each block compares report_only (mask ignores L_cons) with mask_aware on the same tasks; p-values are vs report_only. Mean ± std over seeds.


## Policy: ccppo

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) |
|---|---|---|---|---|---|---|---|---|---|---|
| C0_no_consensus | 99.12 ± 0.53 | 95.67 ± 3.30 | 0.75 ± 0.35 | 0.12 ± 0.18 | 18.84 ± 1.05 | 0.00 ± 0.00 | 0.00 ± 0.00 | 17.15 ± 0.56 | 1372.75 ± 57.42 | 8.95 ± 1.19 |

### edge_x1

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_x1_report_only | 99.12 ± 0.53 | 95.67 ± 3.30 | 0.75 ± 0.35 | 0.12 ± 0.18 | 18.89 ± 1.01 | 0.03 ± 0.00 | 0.00 ± 0.00 | 17.27 ± 0.74 | 1373.13 ± 58.07 | 8.41 ± 0.43 | ref | ref |
| edge_x1_mask_aware | 99.12 ± 0.53 | 95.67 ± 3.30 | 0.75 ± 0.35 | 0.12 ± 0.18 | 18.89 ± 1.01 | 0.03 ± 0.00 | 0.00 ± 0.00 | 17.27 ± 0.74 | 1373.13 ± 58.07 | 8.41 ± 0.43 | 1.000 | 1 |

### edge_x50

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_x50_report_only | 99.25 ± 0.71 | 96.17 ± 4.01 | 0.62 ± 0.53 | 0.12 ± 0.18 | 19.86 ± 1.98 | 1.30 ± 0.02 | 0.00 ± 0.00 | 17.77 ± 0.32 | 1373.31 ± 58.29 | 8.14 ± 0.96 | ref | ref |
| edge_x50_mask_aware | 99.25 ± 0.71 | 96.17 ± 4.01 | 0.62 ± 0.53 | 0.12 ± 0.18 | 19.86 ± 1.98 | 1.30 ± 0.02 | 0.00 ± 0.00 | 17.77 ± 0.32 | 1373.31 ± 58.29 | 8.14 ± 0.96 | 1.000 | 1 |

### edge_cloud_x1

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_cloud_x1_report_only | 99.12 ± 0.53 | 95.67 ± 3.30 | 0.75 ± 0.35 | 0.12 ± 0.18 | 18.89 ± 1.01 | 0.11 ± 0.01 | 0.00 ± 0.00 | 17.15 ± 0.56 | 1373.02 ± 57.92 | 8.41 ± 0.42 | ref | ref |
| edge_cloud_x1_mask_aware | 99.12 ± 0.53 | 95.67 ± 3.30 | 0.75 ± 0.35 | 0.12 ± 0.18 | 18.89 ± 1.01 | 0.11 ± 0.01 | 0.00 ± 0.00 | 17.15 ± 0.56 | 1373.02 ± 57.92 | 8.41 ± 0.42 | 1.000 | 1 |

### edge_cloud_x50

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_cloud_x50_report_only | 95.62 ± 0.88 | 89.17 ± 5.42 | 3.38 ± 0.53 | 1.00 ± 0.35 | 48.65 ± 6.02 | 4.04 ± 0.66 | 0.00 ± 0.00 | 11.49 ± 1.29 | 1358.99 ± 55.28 | 4.82 ± 0.08 | ref | ref |
| edge_cloud_x50_mask_aware | 95.12 ± 1.59 | 89.00 ± 7.07 | 3.75 ± 1.06 | 1.12 ± 0.53 | 48.97 ± 7.83 | 4.21 ± 0.82 | 0.00 ± 0.00 | 11.26 ± 1.31 | 1366.70 ± 66.61 | 4.00 ± 1.23 | 1.000 | 0.34 |

### bft_faulty

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bft_faulty_report_only | 99.00 ± 0.71 | 95.00 ± 4.24 | 0.75 ± 0.35 | 0.25 ± 0.35 | 18.82 ± 1.11 | 0.62 ± 0.02 | 65.00 ± 1.41 | 16.29 ± 0.41 | 1370.72 ± 55.52 | 8.20 ± 0.13 | ref | ref |
| bft_faulty_mask_aware | 99.00 ± 0.71 | 95.00 ± 4.24 | 0.75 ± 0.35 | 0.25 ± 0.35 | 18.82 ± 1.11 | 0.62 ± 0.02 | 65.00 ± 1.41 | 16.29 ± 0.41 | 1370.72 ± 55.52 | 8.20 ± 0.13 | 1.000 | 1 |

## Policy: greedy

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) |
|---|---|---|---|---|---|---|---|---|---|---|
| C0_no_consensus | 99.25 ± 0.35 | 96.67 ± 0.94 | 0.00 ± 0.00 | 0.75 ± 0.35 | 7.20 ± 0.39 | 0.00 ± 0.00 | 0.00 ± 0.00 | 12.97 ± 0.49 | 1358.20 ± 67.89 | 13.12 ± 0.59 |

### edge_x1

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_x1_report_only | 99.12 ± 0.18 | 96.00 ± 0.00 | 0.00 ± 0.00 | 0.88 ± 0.18 | 7.25 ± 0.41 | 0.03 ± 0.00 | 0.00 ± 0.00 | 13.11 ± 0.69 | 1357.61 ± 67.04 | 13.26 ± 0.36 | ref | ref |
| edge_x1_mask_aware | 99.12 ± 0.18 | 96.00 ± 0.00 | 0.00 ± 0.00 | 0.88 ± 0.18 | 7.25 ± 0.41 | 0.03 ± 0.00 | 0.00 ± 0.00 | 13.11 ± 0.69 | 1357.61 ± 67.05 | 13.26 ± 0.36 | 1.000 | 1 |

### edge_x50

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_x50_report_only | 98.50 ± 0.35 | 93.17 ± 0.24 | 0.12 ± 0.18 | 1.38 ± 0.53 | 8.85 ± 0.73 | 1.31 ± 0.01 | 0.00 ± 0.00 | 11.79 ± 0.47 | 1354.30 ± 71.49 | 12.57 ± 0.49 | ref | ref |
| edge_x50_mask_aware | 98.12 ± 0.53 | 91.00 ± 4.24 | 0.50 ± 0.00 | 1.38 ± 0.53 | 8.71 ± 0.23 | 1.30 ± 0.02 | 0.00 ± 0.00 | 11.79 ± 0.12 | 1350.74 ± 57.31 | 12.50 ± 0.35 | 1.000 | 0.55 |

### edge_cloud_x1

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_cloud_x1_report_only | 99.00 ± 0.35 | 95.50 ± 0.71 | 0.12 ± 0.18 | 0.88 ± 0.18 | 7.30 ± 0.48 | 0.09 ± 0.01 | 0.00 ± 0.00 | 12.36 ± 1.05 | 1357.19 ± 65.74 | 13.20 ± 0.31 | ref | ref |
| edge_cloud_x1_mask_aware | 99.00 ± 0.35 | 95.50 ± 0.71 | 0.12 ± 0.18 | 0.88 ± 0.18 | 7.33 ± 0.54 | 0.08 ± 0.00 | 0.00 ± 0.00 | 11.60 ± 0.34 | 1357.12 ± 66.26 | 13.18 ± 0.35 | 1.000 | 1 |

### edge_cloud_x50

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_cloud_x50_report_only | 94.12 ± 0.53 | 75.33 ± 0.94 | 0.62 ± 0.53 | 5.25 ± 1.06 | 14.15 ± 0.64 | 1.94 ± 0.32 | 0.00 ± 0.00 | 2.37 ± 1.09 | 1315.25 ± 70.80 | 6.08 ± 0.47 | ref | ref |
| edge_cloud_x50_mask_aware | 95.38 ± 0.88 | 78.83 ± 0.24 | 0.50 ± 0.00 | 4.12 ± 0.88 | 12.74 ± 0.65 | 1.56 ± 0.08 | 0.00 ± 0.00 | 3.91 ± 0.40 | 1325.60 ± 70.50 | 7.88 ± 2.43 | 0.500 | 0.055 |

### bft_faulty

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bft_faulty_report_only | 98.62 ± 0.18 | 93.67 ± 0.47 | 0.12 ± 0.18 | 1.25 ± 0.35 | 7.62 ± 0.23 | 0.40 ± 0.02 | 40.00 ± 2.83 | 10.13 ± 0.68 | 1352.59 ± 68.05 | 12.95 ± 0.21 | ref | ref |
| bft_faulty_mask_aware | 98.62 ± 0.53 | 93.83 ± 1.18 | 0.12 ± 0.18 | 1.25 ± 0.71 | 7.65 ± 0.15 | 0.37 ± 0.02 | 38.00 ± 2.83 | 9.62 ± 0.65 | 1352.69 ± 73.48 | 12.93 ± 0.44 | 1.000 | 1 |
