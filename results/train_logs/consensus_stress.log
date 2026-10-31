# M14 consensus extension: regime stress

Each block compares report_only (mask ignores L_cons) with mask_aware on the same tasks; p-values are vs report_only. Mean ± std over seeds.


## Policy: ccppo

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) |
|---|---|---|---|---|---|---|---|---|---|---|
| C0_no_consensus | 75.89 ± 1.26 | 40.02 ± 4.41 | 1.22 ± 0.14 | 22.89 ± 1.13 | 29.47 ± 0.78 | 0.00 ± 0.00 | 0.00 ± 0.00 | 22.31 ± 0.79 | 10934.52 ± 210.57 | 10.46 ± 0.28 |

### edge_x1

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_x1_report_only | 75.39 ± 1.15 | 38.72 ± 3.33 | 1.19 ± 0.15 | 23.42 ± 1.23 | 29.19 ± 0.40 | 0.03 ± 0.00 | 0.00 ± 0.00 | 22.45 ± 0.79 | 10927.83 ± 208.73 | 10.17 ± 0.35 | ref | ref |
| edge_x1_mask_aware | 75.39 ± 1.15 | 38.72 ± 3.33 | 1.19 ± 0.15 | 23.42 ± 1.23 | 29.19 ± 0.40 | 0.03 ± 0.00 | 0.00 ± 0.00 | 22.45 ± 0.79 | 10927.83 ± 208.73 | 10.17 ± 0.35 | 1.000 | 1 |

### edge_x10

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_x10_report_only | 75.83 ± 1.21 | 39.47 ± 4.12 | 1.33 ± 0.19 | 22.84 ± 1.10 | 29.19 ± 0.47 | 0.25 ± 0.00 | 0.00 ± 0.00 | 22.06 ± 0.78 | 11041.08 ± 177.40 | 10.10 ± 0.56 | ref | ref |
| edge_x10_mask_aware | 75.83 ± 1.21 | 39.47 ± 4.12 | 1.33 ± 0.19 | 22.84 ± 1.10 | 29.19 ± 0.47 | 0.25 ± 0.00 | 0.00 ± 0.00 | 22.06 ± 0.78 | 11041.08 ± 177.40 | 10.10 ± 0.56 | 1.000 | 1 |

### edge_x50

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_x50_report_only | 74.99 ± 1.23 | 37.47 ± 4.43 | 1.28 ± 0.22 | 23.73 ± 1.14 | 29.13 ± 0.68 | 1.26 ± 0.01 | 0.00 ± 0.00 | 22.42 ± 0.54 | 10873.10 ± 241.38 | 9.63 ± 0.15 | ref | ref |
| edge_x50_mask_aware | 75.13 ± 1.33 | 37.63 ± 4.78 | 1.22 ± 0.20 | 23.65 ± 1.22 | 29.21 ± 0.71 | 1.26 ± 0.01 | 0.00 ± 0.00 | 22.47 ± 0.46 | 10911.72 ± 185.12 | 9.61 ± 0.14 | 1.000 | 0.3 |

### edge_cloud_x1

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_cloud_x1_report_only | 75.17 ± 1.08 | 37.29 ± 3.81 | 1.36 ± 0.09 | 23.48 ± 1.06 | 29.31 ± 0.97 | 0.15 ± 0.00 | 0.00 ± 0.00 | 22.14 ± 0.47 | 10938.20 ± 179.11 | 10.00 ± 0.58 | ref | ref |
| edge_cloud_x1_mask_aware | 75.17 ± 1.08 | 37.29 ± 3.81 | 1.36 ± 0.09 | 23.48 ± 1.06 | 29.31 ± 0.97 | 0.15 ± 0.00 | 0.00 ± 0.00 | 22.14 ± 0.47 | 10938.20 ± 179.11 | 10.00 ± 0.58 | 1.000 | 1 |

### edge_cloud_x10

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_cloud_x10_report_only | 74.39 ± 0.83 | 36.29 ± 3.02 | 1.44 ± 0.05 | 24.17 ± 0.80 | 30.98 ± 1.39 | 1.47 ± 0.04 | 0.00 ± 0.00 | 21.52 ± 0.45 | 10783.11 ± 155.99 | 9.72 ± 0.24 | ref | ref |
| edge_cloud_x10_mask_aware | 74.41 ± 0.81 | 35.77 ± 3.51 | 1.39 ± 0.10 | 24.21 ± 0.79 | 30.64 ± 1.37 | 1.47 ± 0.02 | 0.00 ± 0.00 | 21.46 ± 0.41 | 10812.65 ± 183.40 | 9.41 ± 0.32 | 1.000 | 0.95 |

### edge_cloud_x50

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_cloud_x50_report_only | 65.96 ± 0.63 | 30.13 ± 2.21 | 2.75 ± 0.23 | 31.29 ± 0.67 | 53.96 ± 0.72 | 5.23 ± 0.26 | 0.00 ± 0.00 | 13.02 ± 0.91 | 9496.90 ± 260.32 | 7.98 ± 0.42 | ref | ref |
| edge_cloud_x50_mask_aware | 65.94 ± 0.51 | 31.12 ± 1.58 | 2.72 ± 0.29 | 31.34 ± 0.52 | 53.22 ± 0.42 | 5.16 ± 0.22 | 0.00 ± 0.00 | 12.80 ± 0.58 | 9481.65 ± 164.95 | 8.11 ± 0.23 | 0.938 | 0.96 |

### bft_faulty

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bft_faulty_report_only | 75.30 ± 1.05 | 37.73 ± 3.11 | 1.21 ± 0.08 | 23.49 ± 1.01 | 29.25 ± 1.43 | 0.90 ± 0.02 | 663.40 ± 20.65 | 21.98 ± 0.60 | 10812.70 ± 202.90 | 9.97 ± 0.38 | ref | ref |
| bft_faulty_mask_aware | 75.30 ± 1.05 | 37.73 ± 3.11 | 1.21 ± 0.08 | 23.49 ± 1.01 | 29.25 ± 1.43 | 0.90 ± 0.02 | 663.20 ± 20.71 | 21.98 ± 0.60 | 10812.73 ± 202.89 | 9.97 ± 0.38 | 1.000 | 1 |

## Policy: greedy

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) |
|---|---|---|---|---|---|---|---|---|---|---|
| C0_no_consensus | 88.54 ± 4.54 | 54.37 ± 9.88 | 0.48 ± 0.16 | 10.98 ± 4.48 | 19.51 ± 3.57 | 0.00 ± 0.00 | 0.00 ± 0.00 | 12.96 ± 1.04 | 11967.39 ± 385.05 | 12.29 ± 1.52 |

### edge_x1

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_x1_report_only | 88.11 ± 4.29 | 53.11 ± 9.03 | 0.50 ± 0.17 | 11.39 ± 4.14 | 20.18 ± 3.63 | 0.03 ± 0.00 | 0.00 ± 0.00 | 13.24 ± 1.30 | 11898.84 ± 317.83 | 12.75 ± 1.39 | ref | ref |
| edge_x1_mask_aware | 86.66 ± 4.33 | 50.20 ± 9.71 | 0.62 ± 0.14 | 12.72 ± 4.22 | 21.12 ± 3.06 | 0.03 ± 0.00 | 0.00 ± 0.00 | 13.52 ± 1.26 | 11807.97 ± 331.84 | 12.22 ± 0.96 | 0.500 | 5.1e-17 |

### edge_x10

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_x10_report_only | 87.57 ± 4.03 | 51.68 ± 10.55 | 0.60 ± 0.19 | 11.83 ± 3.88 | 20.58 ± 2.62 | 0.25 ± 0.00 | 0.00 ± 0.00 | 13.19 ± 1.07 | 11913.79 ± 288.41 | 11.91 ± 0.72 | ref | ref |
| edge_x10_mask_aware | 88.19 ± 3.94 | 52.94 ± 8.97 | 0.54 ± 0.15 | 11.27 ± 3.87 | 20.46 ± 3.18 | 0.25 ± 0.00 | 0.00 ± 0.00 | 13.24 ± 0.96 | 11930.78 ± 291.74 | 12.40 ± 1.39 | 0.500 | 0.00081 |

### edge_x50

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_x50_report_only | 85.99 ± 4.05 | 47.32 ± 8.81 | 0.69 ± 0.19 | 13.32 ± 3.89 | 21.52 ± 3.07 | 1.26 ± 0.01 | 0.00 ± 0.00 | 13.88 ± 1.19 | 11830.00 ± 326.71 | 11.51 ± 1.06 | ref | ref |
| edge_x50_mask_aware | 85.25 ± 4.06 | 45.78 ± 9.51 | 0.81 ± 0.19 | 13.94 ± 3.87 | 21.83 ± 2.28 | 1.26 ± 0.01 | 0.00 ± 0.00 | 13.80 ± 1.12 | 11761.12 ± 368.94 | 11.53 ± 0.76 | 0.250 | 0.00026 |

### edge_cloud_x1

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_cloud_x1_report_only | 87.89 ± 3.78 | 53.52 ± 8.38 | 0.61 ± 0.17 | 11.50 ± 3.65 | 20.16 ± 3.39 | 0.10 ± 0.01 | 0.00 ± 0.00 | 13.35 ± 1.08 | 11903.31 ± 340.52 | 12.08 ± 0.55 | ref | ref |
| edge_cloud_x1_mask_aware | 88.49 ± 4.09 | 54.49 ± 7.96 | 0.58 ± 0.15 | 10.93 ± 4.00 | 20.42 ± 3.97 | 0.09 ± 0.01 | 0.00 ± 0.00 | 12.80 ± 0.84 | 11997.65 ± 300.35 | 12.25 ± 0.54 | 1.000 | 0.0011 |

### edge_cloud_x10

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_cloud_x10_report_only | 85.36 ± 4.01 | 44.77 ± 8.75 | 0.59 ± 0.18 | 14.05 ± 3.84 | 21.71 ± 2.84 | 0.94 ± 0.07 | 0.00 ± 0.00 | 12.90 ± 1.05 | 11740.06 ± 418.88 | 10.96 ± 0.73 | ref | ref |
| edge_cloud_x10_mask_aware | 85.95 ± 3.66 | 47.83 ± 8.39 | 0.66 ± 0.26 | 13.39 ± 3.50 | 22.28 ± 2.65 | 0.96 ± 0.06 | 0.00 ± 0.00 | 13.30 ± 1.01 | 11817.86 ± 354.36 | 11.34 ± 0.54 | 0.312 | 0.0037 |

### edge_cloud_x50

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_cloud_x50_report_only | 67.98 ± 1.11 | 22.46 ± 3.25 | 2.50 ± 0.22 | 29.52 ± 0.99 | 52.18 ± 1.10 | 4.11 ± 0.10 | 0.00 ± 0.00 | 8.51 ± 0.38 | 9990.56 ± 138.14 | 8.04 ± 0.46 | ref | ref |
| edge_cloud_x50_mask_aware | 69.04 ± 0.96 | 25.12 ± 2.17 | 2.29 ± 0.24 | 28.67 ± 0.75 | 52.14 ± 1.45 | 3.90 ± 0.18 | 0.00 ± 0.00 | 8.66 ± 0.48 | 9986.61 ± 114.99 | 8.30 ± 0.21 | 0.062 | 0.0003 |

### bft_faulty

| Config | Success (all) % | URLLC on-time % | Late % | Rejected % | Lp95 exec (s) | Mean L_cons (s) | Confirm. failures | Cloud % | Energy (J) | Thr (on-time/s) | p(seed perm) | p(McNemar, pooled) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bft_faulty_report_only | 87.88 ± 4.74 | 53.12 ± 10.39 | 0.64 ± 0.33 | 11.48 ± 4.42 | 20.54 ± 3.55 | 0.52 ± 0.06 | 431.60 ± 31.21 | 13.02 ± 1.10 | 11906.90 ± 321.88 | 12.13 ± 1.57 | ref | ref |
| bft_faulty_mask_aware | 87.50 ± 4.90 | 51.03 ± 11.65 | 0.62 ± 0.30 | 11.88 ± 4.64 | 20.24 ± 3.57 | 0.53 ± 0.06 | 434.00 ± 29.21 | 13.15 ± 1.12 | 11883.44 ± 372.82 | 12.07 ± 1.67 | 0.375 | 0.03 |
