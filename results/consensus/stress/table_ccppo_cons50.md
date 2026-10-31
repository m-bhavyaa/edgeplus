# M14 consensus extension: regime stress

Each block compares report_only (mask ignores L_cons) with mask_aware on the same tasks; p-values are vs report_only. Mean ± std over seeds.


## Policy: ccppo_cons50

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) |
|---|---|---|---|---|---|---|---|---|---|---|
| C0_no_consensus | 74.14 ± 0.98 | 30.26 ± 2.30 | 1.07 ± 0.08 | 24.79 ± 0.96 | 54.75 ± 12.06 | 0.00 ± 0.00 | 0.00 ± 0.00 | 29.45 ± 0.42 | 12245.33 ± 247.81 | 9.38 ± 0.21 |

### edge_x1

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_x1_report_only | 74.24 ± 0.86 | 30.28 ± 2.66 | 0.98 ± 0.05 | 24.78 ± 0.84 | 60.16 ± 0.77 | 0.03 ± 0.00 | 0.00 ± 0.00 | 29.29 ± 0.47 | 12422.18 ± 158.29 | 9.46 ± 0.17 | ref | ref |
| edge_x1_mask_aware | 74.23 ± 0.85 | 30.28 ± 2.45 | 0.93 ± 0.13 | 24.84 ± 0.81 | 59.71 ± 1.68 | 0.03 ± 0.00 | 0.00 ± 0.00 | 29.29 ± 0.38 | 12403.95 ± 46.59 | 9.45 ± 0.15 | 1.000 | 0.96 |

### edge_x10

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_x10_report_only | 74.03 ± 1.22 | 30.16 ± 2.74 | 1.07 ± 0.18 | 24.90 ± 1.05 | 58.69 ± 3.94 | 0.25 ± 0.00 | 0.00 ± 0.00 | 29.24 ± 0.74 | 12392.34 ± 283.55 | 9.35 ± 0.18 | ref | ref |
| edge_x10_mask_aware | 74.13 ± 1.26 | 30.99 ± 3.76 | 1.11 ± 0.15 | 24.76 ± 1.15 | 60.88 ± 0.19 | 0.25 ± 0.00 | 0.00 ± 0.00 | 29.07 ± 0.79 | 12393.44 ± 221.18 | 9.37 ± 0.18 | 1.000 | 0.61 |

### edge_x50

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_x50_report_only | 73.60 ± 0.88 | 29.25 ± 2.85 | 1.01 ± 0.10 | 25.39 ± 0.91 | 61.71 ± 0.29 | 1.26 ± 0.01 | 0.00 ± 0.00 | 29.52 ± 0.55 | 12366.16 ± 221.34 | 9.36 ± 0.19 | ref | ref |
| edge_x50_mask_aware | 73.60 ± 1.25 | 29.24 ± 3.66 | 1.06 ± 0.10 | 25.34 ± 1.19 | 61.39 ± 0.37 | 1.26 ± 0.01 | 0.00 ± 0.00 | 29.37 ± 0.45 | 12328.80 ± 148.62 | 9.36 ± 0.17 | 1.000 | 1 |

### edge_cloud_x1

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_cloud_x1_report_only | 73.97 ± 1.06 | 30.16 ± 2.36 | 1.04 ± 0.17 | 24.99 ± 1.01 | 60.35 ± 2.04 | 0.20 ± 0.01 | 0.00 ± 0.00 | 29.26 ± 0.75 | 12454.73 ± 213.57 | 9.38 ± 0.17 | ref | ref |
| edge_cloud_x1_mask_aware | 74.02 ± 1.07 | 30.30 ± 2.78 | 0.99 ± 0.13 | 24.99 ± 1.01 | 60.40 ± 2.07 | 0.20 ± 0.01 | 0.00 ± 0.00 | 29.24 ± 0.83 | 12420.69 ± 228.37 | 9.55 ± 0.52 | 0.500 | 0.75 |

### edge_cloud_x10

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_cloud_x10_report_only | 73.07 ± 0.71 | 29.43 ± 1.80 | 1.21 ± 0.10 | 25.72 ± 0.76 | 64.43 ± 2.10 | 1.95 ± 0.04 | 0.00 ± 0.00 | 29.07 ± 0.35 | 12199.04 ± 204.87 | 9.39 ± 0.35 | ref | ref |
| edge_cloud_x10_mask_aware | 73.36 ± 1.09 | 29.22 ± 2.57 | 1.12 ± 0.20 | 25.52 ± 1.04 | 60.57 ± 10.01 | 1.97 ± 0.04 | 0.00 ± 0.00 | 28.92 ± 0.53 | 12257.81 ± 277.33 | 9.33 ± 0.40 | 0.250 | 0.31 |

### edge_cloud_x50

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_cloud_x50_report_only | 64.31 ± 0.97 | 23.08 ± 1.69 | 2.26 ± 0.19 | 33.43 ± 0.88 | 74.41 ± 9.98 | 6.75 ± 0.45 | 0.00 ± 0.00 | 17.01 ± 0.89 | 10472.94 ± 176.90 | 7.77 ± 0.49 | ref | ref |
| edge_cloud_x50_mask_aware | 65.03 ± 1.16 | 25.51 ± 1.94 | 2.20 ± 0.11 | 32.77 ± 1.21 | 80.17 ± 8.62 | 6.50 ± 0.39 | 0.00 ± 0.00 | 16.06 ± 1.42 | 10636.39 ± 77.60 | 7.82 ± 0.28 | 0.062 | 0.022 |

### bft_faulty

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bft_faulty_report_only | 73.65 ± 0.61 | 29.54 ± 2.29 | 1.12 ± 0.15 | 25.23 ± 0.56 | 58.08 ± 14.08 | 1.27 ± 0.02 | 920.60 ± 12.50 | 29.25 ± 0.47 | 12336.44 ± 231.08 | 9.31 ± 0.12 | ref | ref |
| bft_faulty_mask_aware | 73.62 ± 0.70 | 29.30 ± 2.18 | 1.07 ± 0.06 | 25.31 ± 0.70 | 58.35 ± 13.35 | 1.26 ± 0.02 | 906.40 ± 18.49 | 28.87 ± 0.88 | 12244.49 ± 97.14 | 9.50 ± 0.30 | 0.750 | 0.93 |
