# EdgePlus re-implementation (semester project)

A simplified, documented re-implementation of **EdgePlus: A Multiagent Reinforcement Learning Framework for Dynamic Task Allocation in 6G Edge Computing** (Taher et al., IEEE IoT-J 13(8), 2026), plus one research extension: **consensus-delay-aware feasibility**.

This is **not** an exact reproduction. The paper's Brașov dataset, plant parameters and many hyperparameters are not available, so our numbers cannot be compared one-to-one with the paper's. Every assumption is listed in [`docs/assumptions.md`](docs/assumptions.md). Results and their interpretation are in [`reports/report_draft.md`](reports/report_draft.md).

## What is implemented

| Milestone | What | Where |
|---|---|---|
| M1–M5 | 10-cluster topology; stationary, mobile and cloud servers; Poisson workload with the paper's deadline bands and class shares; FIFO queues; Eq. 1–4 latency, energy and slice feasibility; masks; explicit outcomes | `env/` |
| M6 | Random feasible baseline (and a greedy sanity baseline) | `agents/baselines.py` |
| M7 / M8 | SB3 PPO (unmasked) / MaskablePPO | `agents/sb3_train.py`, `train_m7_ppo.py`, `train_m8_masked_ppo.py` |
| M9 | CCPPO: 10 cluster actors with shared parameters, local observations, centralized critic, masked softmax, GAE, clip, entropy, KL | `agents/ccppo.py`, `train_m9_ccppo.py` |
| M10 | Advisory layer: Nash best response, PID (ZN init + Jury test), leader election, logit bias | `advisory/` |
| M11 | Constricted PSO (Eq. 13), SLA-gated, tunes advisory gains, disabled at evaluation | `optimizer/pso.py` |
| M12 | Ledger simulator: Eq. 18 log tuples, hash-chained partial blocks (SHA3→BLAKE2b), adaptive block size, PoA validation, periodic BFT, reputation, debt, URLLC quarantine | `ledger/ledger.py` |
| M13 | Integrated runs and ablations A1–A6 | `run_edgeplus.py` |
| M14 | Consensus-delay model (synchronous-commit assumption); report_only vs mask_aware; edge vs edge+cloud; delay sweep; broken BFT quorum | `ledger/consensus.py`, `run_consensus_extension.py` |
| M15 | CMDP design only (**not implemented**) | `reports/m15_cmdp_design.md` |
| OBJ6 | PID ±20 % drift robustness | `experiments/obj6_pid.py` |

Not implemented: real cryptography, DKMS, attack experiments (OBJ7), CBS–D* Lite path planning, and the paper's other baselines (ensemble PPO, FD3QN, DDPG, SAC).

## Layout
```
configs/base.json        all parameters (dotted overrides, e.g. "workload.regime")
env/                     simulator core, workload, servers, Gym wrapper, factory
agents/                  baselines, SB3 wrappers, CCPPO
advisory/ optimizer/ ledger/
evaluation/              paired evaluator, KPIs, stats, Markdown tables
diagnostics/             per-task constraint breakdown
experiments/             presets (baseline, ablations, consensus variants), OBJ6
tests/                   pytest suite
models/                  checkpoints (+ .json metadata, .log.json training curves)
results/                 summaries and tables (per-task CSVs are regenerated, not committed)
reports/                 audit, report draft, M15 design
```

## Install
Python 3.11 (tested with 3.11.15, CPU only).
```
python3 -m venv .venv && . .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

## Test
```
python -m pytest            # 61 tests, ~4 s
```

## Train (CPU times measured in this repo)
```
python train_m7_ppo.py --timesteps 100000            # ~1 min
python train_m8_masked_ppo.py --timesteps 100000     # ~1.5 min
python train_m9_ccppo.py --timesteps 60000                                   # m9_ccppo.pt (masks+advisory+ledger)
python train_m9_ccppo.py --no-advisory --out models/m9_ccppo_noadv.pt
python train_m9_ccppo.py --no-ledger   --out models/m9_ccppo_noledger.pt
python train_m9_ccppo.py --no-masks    --out models/m9_ccppo_nomask.pt
python train_m9_ccppo.py --no-masks --no-advisory --no-ledger --out models/m9_ccppo_plain.pt
python train_m9_ccppo.py --no-advisory --no-ledger --out models/m9_ccppo_maskonly.pt
# follow-ups (report §8, §10)
python train_m9_ccppo.py --set ledger.quarantine=false --out models/m9_ccppo_noquar.pt
python train_m9_ccppo.py --set reward.eta6=0 reward.eta7=0 --out models/m9_ccppo_noshape.pt
python train_m9_ccppo.py --set seeds.train_base=11000 --out models/m9_ccppo_s2.pt
python train_m9_ccppo.py --no-ledger --set seeds.train_base=11000 --out models/m9_ccppo_noledger_s2.pt
python train_m9_ccppo.py --set 'consensus.mode="mask_aware"' 'consensus.path="edge_cloud"' consensus.delay_scale=50 --out models/m9_ccppo_cons50.pt
```
Add `--smoke` to any training script to check the pipeline in a few seconds. A smoke model is **not** a result.

## Reproduce every table
| Table (report section) | Command | Output |
|---|---|---|
| §7 baselines M6–M9 | `python evaluate_baselines.py --regime {light,medium,stress}` | `results/baselines/<regime>/table.md` |
| §8 ablations A1–A6 | `python run_edgeplus.py --regime {medium,stress}` | `results/edgeplus/<regime>/table.md`, `pso.json` |
| §8 ungated PSO | `python run_edgeplus.py --regime stress --pso-ungated --only A1_full A2_no_pso` | `results/edgeplus/stress_pso_ungated/` |
| §9 PID robustness | `python -m experiments.obj6_pid` | `results/obj6/summary.json`, `grid.csv` |
| §8 ledger follow-up | `python -m experiments.ledger_ablation --regime stress` | `results/ledger_ablation/stress/table.md` |
| §10 consensus extension | `python run_consensus_extension.py --regime stress` (~7 min) | `results/consensus/stress/table.md` |
| §10 consensus-trained CCPPO | `python run_consensus_extension.py --regime stress --policies ccppo_cons50` | `results/consensus/stress/table_ccppo_cons50.md` |

Each output folder contains `summary.json` (per-seed and aggregate KPIs, git commit), `config.json`, and per-task / per-server CSVs (`tasks_seed*.csv`, `servers_seed*.csv`). Add `--smoke` (2 seeds × 400 tasks) to any runner for a quick check.

**Seeds:** evaluation 38–42; training 10000+; PSO 20000+ (disjoint). Every policy is evaluated on the same regenerated workload for each seed.

**Metric conventions:** `success_all` = on-time / offered tasks. Rejected tasks count as violations. `*_exec` metrics (latency percentiles, cloud share, locality) are computed over executed tasks only. The evaluator raises an error if the number of recorded outcomes differs from the number of offered tasks.

## Pre-audit code
The original M1–M8 code and its results are kept at git tag `preliminary-v0`, with the numbers frozen in `results/preliminary/README.md`. The audit that motivated the rewrite is in `reports/phase_a_audit.md`. The old checkpoints are `models/legacy_*.zip`. They need the old 125-dimensional observation, so they only run at that tag.
