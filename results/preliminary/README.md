# Preliminary results (pre-audit, frozen)

These numbers were produced by the code at commit `cb22869` (branch `main`) before any Phase A/B change. They are kept here unchanged so later results can be compared against them. They come from a simplified simulator and are **not** a reproduction of the paper's reported numbers.

Re-run on 2026-10-31 in this sandbox (Python 3.11.15, numpy 2.4.6, gymnasium 1.4.0, stable-baselines3 2.9.2, sb3-contrib 2.9.2, torch 2.15.0+cpu). Every number below matched the values the user recorded earlier.

| Run | Checkpoint | Eval workload seed | Tasks | Success | Mean latency* | P50* | P95* | Mean reward | Mean energy* | Zero-feasible tasks |
|---|---|---|---|---|---|---|---|---|---|---|
| M6 random feasible | n/a (policy RNG seed = workload seed) | 42 | 1000 | 91.50% | 3.8394 s | 3.3195 s | 8.2501 s | 5.6369† | 1.8627 | 85 |
| M6 random feasible | n/a | 100 | 1000 | 91.20% | 4.0727 s | 3.5471 s | 8.9346 s | 5.4057† | 1.8750 | 88 |
| M7 PPO (unmasked) | `models/m7_ppo.zip` | 100 | 1000 | 26.30% | 4.3967 s | 3.4773 s | 10.9431 s | -5.8963 | 1.1628 | 28 |
| M8 MaskablePPO | `models/m8_masked_ppo.zip` | 100 | 1000 | 87.40% | 6.3373 s | 6.0436 s | 12.0044 s | 1.9412 | 1.6461 | 126 |

\* Computed over **successful tasks only**.
† M6 skips `env.execute` when no server is feasible, so those tasks add 0 reward instead of -10. M6 reward is therefore not comparable with M7/M8 reward (audit defect D12).

Notes:
- The committed `evaluate-m7.py` loads `models/m8_masked_ppo` and crashes with the current SB3 versions (defect D1). The M7 row above was produced by the same script with the path changed to `models/m7_ppo`. Its output matches the recorded M7 numbers exactly, so those numbers came from the real M7 checkpoint.
- Both checkpoints were trained on one fixed 500-task workload (seed 42), replayed in every episode (defect D9).

Reproduce (from the repository root, with the virtualenv active):
```
python experiment-m6.py                      # seed 42 row
python evaluate-m8.py                        # M8 row
sed 's#models/m8_masked_ppo#models/m7_ppo#' evaluate-m7.py > /tmp/eval_m7.py && PYTHONPATH=. python /tmp/eval_m7.py
```
