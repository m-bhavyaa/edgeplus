# EdgePlus re-implementation: complete project overview

**Course:** third-year B.Tech semester project (research-oriented)
**Paper studied:** B. H. Taher, J. Luo, F. Ghrabat, Y. Qiao, *"EdgePlus: A Multiagent Reinforcement Learning Framework for Dynamic Task Allocation in 6G Edge Computing"*, IEEE Internet of Things Journal, vol. 13, no. 8, April 2026.

This document describes the whole project from start to finish: what the paper proposes, how we rebuilt it, what we changed or simplified, the two research extensions we added, every result we measured, and how to reproduce each one.

> **Honesty statement.** This is a *simplified re-implementation*, not an exact reproduction. The paper's dataset (Brașov air-quality traces), simulator, plant parameters and many hyperparameters are not public, so our numbers are **not** comparable one-to-one with the paper's. Every number in this README comes from running the code in this repository. Nothing is copied from the paper unless it is explicitly marked **[PAPER]**. All assumptions are listed in [`docs/assumptions.md`](docs/assumptions.md).

---

## Contents
1. [The problem](#1-the-problem)
2. [What the paper proposes](#2-what-the-paper-proposes)
3. [What we did, step by step](#3-what-we-did-step-by-step)
4. [System architecture](#4-system-architecture)
5. [Component by component: paper vs our implementation](#5-component-by-component-paper-vs-our-implementation)
6. [Experimental setup](#6-experimental-setup)
7. [Results: reproduction of the EdgePlus method](#7-results-reproduction-of-the-edgeplus-method)
8. [Results: our research extensions](#8-results-our-research-extensions)
9. [Key findings](#9-key-findings)
10. [Limitations and threats to validity](#10-limitations-and-threats-to-validity)
11. [How to run everything](#11-how-to-run-everything)
12. [Repository map](#12-repository-map)
13. [References](#13-references)

---

## 1. The problem
In a smart city, thousands of IoT sensors (for example air-quality sensors on lampposts) produce readings that must be processed by a **deadline**. Each reading is a *task*. Edge servers sit in each city cluster, some servers are mobile (vehicles), and a remote cloud exists. For every arriving task, a scheduler must choose **which server runs it**, so that:
- the task finishes before its deadline (on time),
- servers, network slices and energy budgets are not overloaded,
- the system stays secure and auditable (who ran what, and was it on time).

Tasks belong to three 6G service classes, with the deadlines from the paper (Sec. IV-B):

| Class | Meaning | Deadline (relative to arrival) | Share of tasks |
|---|---|---|---|
| URLLC | ultra-reliable low-latency | U[5, 15] s | 20 % |
| eMBB | enhanced mobile broadband | U[30, 120] s | 50 % |
| mMTC | massive machine-type | U[120, 600] s | 30 % |

## 2. What the paper proposes
EdgePlus is a "feasibility-first" scheduler with four layers:

1. **Masked cooperative PPO (CCPPO)**: one reinforcement-learning actor per cluster, plus a *centralized critic* that sees the whole system during training. A **feasibility mask** removes every server that would break a rule (routing order, slice budget, memory, energy, deadline) *before* the policy samples, so the policy can only choose valid servers.
2. **Advisory layer**: three small controllers add a *bias* to the policy's scores without overriding the mask:
   - **Nash sharing**: clusters decide how much work to share.
   - **PID controller**: keeps each cluster's utilisation near a set-point. Initial gains come from Ziegler–Nichols tuning and are checked with the Jury stability test.
   - **Leader election**: favours the least-loaded server in each cluster.
3. **Constricted particle swarm optimisation (PSO)**: an outer optimisation loop that tunes higher-level parameters. A new setting is accepted only if it passes service-level (SLA) checks.
4. **Blockchain-lite ledger**: edge clusters log completed tasks into hash-chained blocks validated by Proof-of-Authority (PoA). The cloud finalises them with Byzantine Fault Tolerance (BFT). The ledger computes each server's **reputation** and each cluster's **debt**, and these feed back into the scheduler's state, reward and mask.

**[PAPER]** headline result at the 150k-task stress load: 82.77 % on-time success, 17.23 % violations. Removing masks costs 5.5–10 pp.

## 3. What we did, step by step

| Phase | Work | Output |
|---|---|---|
| **A. Audit** | Read the paper; audited our earlier M1–M8 code; found 20 defects. Examples: a wrong checkpoint in the M7 evaluation; an absolute time fed to the policy as "queue"; processing starting before the data arrived; the M8 "100 % success on feasible tasks" being true by construction | [`reports/phase_a_audit.md`](reports/phase_a_audit.md); old code frozen at git tag `preliminary-v0`; old numbers in [`results/preliminary/`](results/preliminary/README.md) |
| **B. Stabilise** | Rewrote the simulator to follow the paper: routing tiers, mobile and cloud servers, energy (Eq. 2), slice budgets (Eq. 4), correct timing, explicit outcomes for every task, paper deadlines and class shares, scaled observations, and a new workload every training episode | `env/` |
| **C. Components** | M9 CCPPO, M10 advisory layer, M11 PSO, M12 ledger, each with its own tests | `agents/`, `advisory/`, `optimizer/`, `ledger/` |
| **D. Integrate** | One evaluator that runs every policy on identical workloads; ablations A1–A6 from the paper's Table VI; PID robustness test (paper OBJ6) | `evaluation/`, `run_edgeplus.py`, `experiments/obj6_pid.py` |
| **E. Extension 1** | **Consensus-delay-aware feasibility**: what if ledger confirmation had to finish *before* a task is dispatched? | `ledger/consensus.py`, `run_consensus_extension.py` |
| **Follow-ups** | Why ledger feedback seemed to hurt; CCPPO trained under consensus delay | `experiments/ledger_ablation.py` |
| **E. Extension 2** | **Per-sensor energy preservation**: battery-powered sensors with solar harvesting and a Lyapunov energy price (suggested by our teacher) | `env/sensors.py`, `experiments/sensor_energy.py` |
| **F. Finalise** | 68 automated tests; every script checked; documentation; report draft | `tests/`, [`reports/report_draft.md`](reports/report_draft.md) |

## 4. System architecture

```
                         ┌───────────────── configs/base.json (all parameters) ─────────────────┐
                         ▼                                                                       ▼
 Task generator ──► EdgePlus simulator (env/edge_env.py) ◄──────── Ledger simulator (ledger/)
 (Poisson arrivals,   │ 1. routing tiers: local stationary → local mobile        │  log tuple at task end
  paper deadlines,    │    → neighbour mobile → cloud                            │  hash-chained blocks, PoA
  sensor id)          │ 2. feasibility mask: slice, memory, energy, deadline,    │  periodic cloud BFT
                      │    reputation, (battery)                                 │  reputation ρ, debt d ──┐
 Sensor batteries ───►│ 3. latency = consensus + tx + move + queue + processing  │                         │
 (env/sensors.py)     │ 4. outcome: on_time | late | rejected | dropped_battery  │                         │
                      │ 5. reward (Eq. 7) + ledger shaping (Eq. 15) + energy price                         │
                      ▼                                                                                    │
           Policy chooses a server  ◄── masked softmax (Eq. 10) ◄── logits + advisory bias (Eq. 9) ◄───────┘
           ├─ M6 random feasible / greedy           ├─ Nash sharing (advisory/nash.py)
           ├─ M7 PPO / M8 MaskablePPO (SB3)         ├─ PID + ZN + Jury (advisory/pid.py)
           └─ M9 CCPPO: 10 cluster actors +         └─ leader election (advisory/leader.py)
              centralized critic (agents/ccppo.py)
                      ▲
           PSO outer loop (optimizer/pso.py): tunes advisory gains, SLA-gated, OFF during evaluation
                      │
           Evaluator (evaluation/): same seeds for every policy → per-task CSV, KPIs, tables, statistics
```

## 5. Component by component: paper vs our implementation

| Component | Paper | Our implementation | Status |
|---|---|---|---|
| Topology | 10 clusters (K-means + Delaunay), 100 km² | 10-cluster grid, fixed adjacency, 1 unit = 1 km | approximation |
| Servers | stationary + mobile + cloud | 2 stationary (1 and 2 GHz) + 1 mobile (1.5 GHz, 120 km/h) per cluster, 1 cloud (10 GHz) = 31 servers | assumed counts |
| Workload | Brașov traces → tasks | Synthetic Poisson arrivals with the paper's deadline bands and shares | approximation |
| Latency (Eq. 1) | tx + move + queue + proc | Same four terms; FIFO queue; transmission overlaps queueing; random service-time noise | approximation |
| Routing order (III-C) | stationary c(i) → mobile c(i) → mobile N(c(i)) → cloud | Same | faithful |
| Slice budgets (Eq. 4) | radio and compute time budgets per cluster and class | compute part only | partial |
| Energy (Eq. 2–3) | tx + movement + compute; budget on mobiles | Same structure; constants assumed | faithful structure |
| Masks | hard; deadline hard for URLLC | Same; zero-feasible tasks rejected explicitly | faithful |
| Reward (Eq. 7, 15) | on-time, late, latency, energy, cloud, reputation, debt | Same terms; η values assumed | faithful structure |
| CCPPO (III-E) | cooperative actors + centralized critic, GAE, clip, entropy, KL | 10 cluster actors with shared weights, local observations, global critic | documented interpretation |
| Advisory (Eq. 9, 11) | Nash, PID, leader bias the logits | Same; Nash coupling and PID sign chosen by us | faithful structure |
| PID robustness (Eq. 17) | ZN init, Jury test over ±20 % gain corners | Same; plant parameters assumed | faithful method |
| PSO (Eq. 13) | constricted PSO with inertia, SLA-gated | Exactly as printed; tunes the 3 advisory gains | partial scope |
| Ledger (Eq. 18–29) | PoA partial blocks, BFT finality, reputation EMA, debt, quarantine | Simulated with real SHA3/BLAKE2b hashing; delays modelled; no real signatures or encryption | simulation |
| Security / DKMS / attacks (OBJ7) | AES-GCM, X25519, Ed25519, key rotation, attack tests | not implemented | out of scope |
| Mobility planning (Alg. 4) | CBS–D* Lite | straight-line travel | simplified |
| Other baselines | ensemble PPO, FD3QN, DDPG, SAC | random, greedy, PPO, MaskablePPO instead | substituted |
| Consensus-aware feasibility | — | Extension 1 | **ours** |
| Per-sensor batteries | — | Extension 2 | **ours** |
| CMDP safety | future work in the paper | design document only ([`reports/m15_cmdp_design.md`](reports/m15_cmdp_design.md)) | not implemented |

## 6. Experimental setup
- **Load regimes:** light, medium and stress = 6, 12 and 18 tasks/s over a 200 s episode (1200, 2400 and 3600 tasks). The system's nominal capacity is about 16 tasks/s, so "stress" is deliberately overloaded.
- **Seeds:** evaluation 38, 39, 40, 41, 42 (the paper uses 38–40). Training seeds 10000+ and PSO seeds 20000+, all disjoint. **Every policy sees exactly the same tasks for each evaluation seed.**
- **Training:** CPU only. M7 and M8: 100k steps (about 1 min each). CCPPO: 60k steps (about 1.5 min). This is a small budget.
- **Metric conventions:**
  - Success = on-time tasks / *all offered* tasks. Rejected and dropped tasks count as failures.
  - Latency percentiles and cloud share are computed over *executed* tasks only.
  - Tables show mean ± standard deviation over the 5 seeds.
- **Statistics:** paired sign-flip permutation test over seeds. With 5 seeds the smallest possible p-value is 0.0625, so "p = 0.06" means all 5 seeds moved in the same direction. The pooled per-task McNemar values in the raw tables are **not** valid evidence (explained in §10).

## 7. Results: reproduction of the EdgePlus method

### 7.1 Baselines M6–M9
Simulator without ledger or advisory. Source: `results/baselines/<regime>/table.md`.

| Policy | Light success % | Medium success % | Stress success % | Stress Lp95 (s) | Stress cloud % |
|---|---|---|---|---|---|
| M6 random feasible | 97.17 ± 0.57 | 94.59 ± 1.03 | 74.42 ± 0.90 | 62.2 | 25.0 |
| Greedy (lowest predicted latency) | 100.00 ± 0.00 | 99.92 ± 0.05 | 88.54 ± 4.54 | 19.5 | 13.0 |
| M7 PPO, no mask | 57.75 ± 0.75 | 35.43 ± 0.93 | 27.45 ± 0.37 | 33.9 | 98.7 |
| M8 MaskablePPO | 99.28 ± 0.36 | 98.12 ± 0.38 | 73.74 ± 1.02 | 31.7 | 17.8 |
| M9 CCPPO, masks only | 99.48 ± 0.18 | 98.52 ± 0.25 | 74.18 ± 0.85 | 30.3 | 18.1 |

- Without masks, PPO learns to send almost everything to the cloud and loses most tasks to invalid choices.
- With masks, the learned policies beat random at light and medium load, but not at stress.
- A simple greedy rule beats every learned policy. With our small training budget, RL has not learned to use the predicted-latency feature as well as a direct "pick the minimum" rule.

### 7.2 Ablations A1–A6 (paper Table VI)
Source: `results/edgeplus/<regime>/table.md`.

| Config | Masks | Advisory | PSO | Ledger | Medium success % | Stress success % | Stress Lp95 (s) | **[PAPER]** stress % |
|---|---|---|---|---|---|---|---|---|
| A1 full | ✓ | ✓ | ✓ | ✓ | 99.48 ± 0.21 | 75.89 ± 1.26 | 29.5 | 82.8 |
| A2 no PSO | ✓ | ✓ | – | ✓ | 99.48 ± 0.21 | 75.89 ± 1.26 | 29.5 | 82.0 |
| A3 no advisory | ✓ | – | ✓ | ✓ | 98.49 ± 0.42 | 73.75 ± 0.88 | 34.3 | 80.0 |
| A4 no ledger | ✓ | ✓ | ✓ | – | 99.39 ± 0.15 | 77.68 ± 0.98 | 27.1 | 82.8 |
| A5 no masks | – | ✓ | ✓ | ✓ | 73.97 ± 0.72 | 58.43 ± 1.16 | 28.0 | 77.3 |
| A6 plain CCPPO | – | – | – | – | 77.53 ± 0.36 | 58.56 ± 0.69 | 27.9 | 72.8 |

- **Masks dominate**, as the paper says: removing them costs about 17 pp at stress and 22–26 pp at medium.
- **Advisory helps**: +2.1 pp at stress, +1.0 pp at medium, in all 5 seeds.
- **PSO with the paper's SLA gate never accepted a new setting.** Cloud share (about 17 %) and failure rate (about 8 %) always broke the gate's limits (≤ 7 %, ≤ 5 %), so A1 = A2. Without the gate (`--pso-ungated`), PSO adds +1.35 pp (77.24 %) and lowers Lp95 from 29.5 to 26.5 s.
- **Ledger:** A4 > A1 looked like "the ledger hurts". The follow-up in §8.1 shows this was training randomness.
- Ledger cost (seed 38, stress): 2311 edge blocks, 0 rejected, PoA validation median 0.10 ms, BFT median 7.1 ms, 0 BFT timeouts.

### 7.3 PID robustness (paper OBJ6)
Source: `results/obj6/summary.json`. Our plant is assumed (K = 1, τ = 2 s, L = 0.5 s), so these numbers are not comparable with the paper's 2.74 s.

| Gains (Kp, Ki, Kd) | Nominal settling / overshoot | ±20 % corners passing |
|---|---|---|
| Ziegler–Nichols (4.8, 4.8, 1.2) | 31 s / 116 % | 0 / 8 |
| Paper's best (1.9, 1.2, 0.06) | 4.1 s / 21.6 % | 2 / 8 |
| Paper's gains after our "shrink all gains" certification (0.91, 0.57, 0.029) | 8.0 s / 3.7 % | **8 / 8** |

The paper's certification rule (reduce only Kp) did not converge on our plant. Shrinking all three gains did.

## 8. Results: our research extensions

### 8.1 Follow-up: does ledger feedback help or hurt?
Source: `results/ledger_ablation/stress/table.md`.

| Variant (stress) | Success % |
|---|---|
| Ledger on (full) | 75.89 ± 1.26 |
| Quarantine off at evaluation only | 75.93 ± 1.26 |
| Trained without quarantine | 75.80 ± 1.10 |
| Trained without reputation/debt reward terms | 75.58 ± 1.03 |
| Ledger off | 77.68 ± 0.98 |
| The ledger-off model run **with** the ledger on | 77.70 ± 0.91 |
| Ledger on, 2nd training seed | 76.87 ± 0.66 |
| Ledger off, 2nd training seed | 76.08 ± 1.15 |

**Conclusion:** the ledger's run-time effect is less than 0.3 pp. The gap came from which network happened to be trained, and it reverses with a second training seed. Training-seed noise is about ±1 pp, so we cannot rank configurations that differ by less than about 1–2 pp.

### 8.2 Extension 1: consensus-delay-aware feasibility
**Research question.** Can accounting for ledger-consensus delay in the feasibility check improve deadline reliability without large losses in latency, energy or throughput?

**Important distinction.** In the paper, the ledger logs a task *after* it finishes, and cloud BFT is *off the critical path*, so consensus never delays a task. We therefore study a **hypothetical** transaction model: an assignment is dispatched only after it has been committed to the ledger.
- `edge` path: wait for the edge block to seal, then PoA validation.
- `edge_cloud` path: placements outside the home cluster also wait for the next BFT round.
- `report_only`: consensus delay adds to latency, but the mask ignores it.
- `mask_aware`: the mask also includes the expected delay in the deadline check.
- We sweep the delay scale (×1 = paper-like, ×10, ×50) and also test a broken BFT quorum (2 of 4 replicas faulty).

Results at stress, report_only → mask_aware. Source: `results/consensus/stress/table*.md`.

| Scenario | Mean consensus delay | CCPPO | Greedy | CCPPO trained with delay (×50) |
|---|---|---|---|---|
| No consensus | 0 s | 75.89 | 88.54 | 74.14 |
| edge ×1 | 0.03 s | 75.39 → 75.39 | 88.11 → 86.66 | 74.24 → 74.23 |
| edge ×10 | 0.25 s | 75.83 → 75.83 | 87.57 → 88.19 | 74.03 → 74.13 |
| edge ×50 | 1.26 s | 74.99 → 75.13 | 85.99 → 85.25 | 73.60 → 73.60 |
| edge+cloud ×1 | 0.1–0.2 s | 75.17 → 75.17 | 87.89 → 88.49 | 73.97 → 74.02 |
| edge+cloud ×10 | 0.9–2.0 s | 74.39 → 74.41 | 85.36 → 85.95 | 73.07 → 73.36 |
| edge+cloud ×50 | 3.9–6.8 s | 65.96 → 65.94 | 67.98 → **69.04** | 64.31 → **65.03** |
| BFT quorum broken | 0.5–1.3 s | 75.30 → 75.30 | 87.88 → 87.50 | 73.65 → 73.62 |

**Answer.** At realistic, paper-scale delays, a consensus-aware mask makes no measurable difference. It helps a little only when synchronous confirmation adds seconds of delay (edge+cloud ×50): +1.1 pp for greedy, and +0.7 pp success and +2.4 pp URLLC on-time for a CCPPO trained under that delay. Both effects have p = 0.0625, the smallest possible with 5 seeds.

### 8.3 Extension 2: per-sensor energy preservation
**Motivation.** The paper motivates EdgePlus with battery-powered sensors, but only limits the energy of *mobile servers*. Our teacher suggested modelling energy per sensor.

**Model** (`env/sensors.py`, off by default):
- 200 sensors (20 per cluster), each with a 1.2 J battery that starts 20–100 % full.
- Solar harvesting follows a day/night sine curve (one compressed "day" = one 200 s episode).
- Taking a reading costs 0.01 J. Uploading costs P_tx × airtime, so a slow link drains the sensor more. The cloud's wired backhaul is free for the sensor.
- **Battery mask:** a server is infeasible if the sensor can't afford the upload to it. A dead sensor drops its reading (`dropped_battery` outcome).
- **Lyapunov virtual energy queue** per sensor, following the "drift-plus-penalty" method used in energy-harvesting MEC work such as LODCO [2]: Z ← max(Z + energy spent − sustainable budget, 0). A large Z means "this sensor is overspending". The upload is then priced at V · Z · E_upload.
- Policies:
  - **Lyapunov greedy**: minimise latency/slack + V · price.
  - **CCPPO trained with the price in its reward** (λ_E = 1).
  - **CCPPO with the price as a logit bias** at inference.

Results. Source: `results/sensor_energy/<regime>/table.md`.

| Stress (18 tasks/s) | Success % | Readings dropped % | Sensors that died % | Battery left % | Battery fairness | Lp95 (s) |
|---|---|---|---|---|---|---|
| E0 greedy, no battery limit (reference) | 88.54 | 0 | n/a | n/a | n/a | 19.5 |
| E1 greedy, energy-unaware | 86.21 ± 3.40 | 4.34 | 21.4 | 26.6 | 0.55 | 17.8 |
| **E2 Lyapunov greedy, V = 1** | **86.51 ± 3.31** | **2.81** | **16.1** | 29.4 | 0.61 | 21.6 |
| E3 Lyapunov greedy, V = 5 | 82.56 ± 2.45 | 1.91 | 10.5 | 32.5 | 0.65 | 27.8 |
| E4 CCPPO, no energy price | 75.78 ± 1.24 | 2.59 | 13.5 | 33.8 | 0.64 | 32.1 |
| E5 CCPPO, Lyapunov reward | 77.42 ± 1.38 | 2.68 | 16.0 | 31.5 | 0.61 | 54.0 |
| E6 CCPPO + Lyapunov bias | 75.74 ± 1.39 | 2.36 | 13.1 | 33.7 | 0.64 | 32.1 |

| Medium (12 tasks/s) | Success % | Dropped % | Sensors died % | Battery left % | Lp95 (s) |
|---|---|---|---|---|---|
| E1 greedy, energy-unaware | 99.43 ± 0.26 | 0.35 | 2.1 | 50.1 | 5.6 |
| **E2 Lyapunov greedy, V = 1** | **99.66 ± 0.15** (p = 0.06) | 0.21 | 1.2 | 51.4 | 6.5 |
| E3 Lyapunov greedy, V = 5 | 99.61 ± 0.13 | 0.17 | 1.0 | 52.1 | 9.4 |

**Findings:**
- **Pricing sensor energy with a Lyapunov queue preserves batteries.** At stress, V = 1 cuts sensor deaths from 21.4 % to 16.1 % and dropped readings from 4.3 % to 2.8 %, with no loss in success. At medium it even raises success slightly, in all 5 seeds.
- **V is an explicit trade-off knob.** V = 5 halves sensor deaths again (10.5 %) but costs 3.7 pp of success and about 10 s of tail latency, because cheap links (cloud, fast servers) are not always the fastest.
- **The learned version did not work as well.** Adding the price to CCPPO's reward raised success by 1.6 pp but did *not* reduce deaths, and it doubled tail latency. The logit bias had no measurable effect. With our training budget, the simple rule beats the learned policy here too.

## 9. Key findings
1. **Feasibility masks matter most.** This confirms the paper's main claim in our setting.
2. The advisory layer gives a small but consistent gain (+1–2 pp).
3. PSO under the paper's SLA gate was never accepted. Without the gate it helped slightly.
4. Ledger feedback has no effect that we can separate from training-seed noise.
5. A simple greedy heuristic outperformed all learned policies at our training budget. This is an important caveat for any RL claim.
6. Consensus-aware masks only matter when confirmation sits on the dispatch path and takes seconds.
7. Per-sensor Lyapunov energy pricing extends sensor life at little or no cost to success (V = 1), and gives a tunable lifetime-vs-latency trade-off.

## 10. Limitations and threats to validity
- **Simulator:** synthetic workload and topology. FIFO queues where the scheduler knows the true backlog. No radio channel (Shannon) model and no path planning. No real cryptography and no security experiments (paper OBJ7).
- **Training:** small CPU budgets and mostly one training seed per model. Differences below about 1–2 pp are within training noise (§8.1).
- **Statistics:** 5 evaluation seeds, so the minimum p is 0.0625. Per-task McNemar p-values look tiny but are invalid: one different early decision changes the entire queue afterwards, so tasks are not independent.
- **Extension 1** uses a hypothetical synchronous-commit model that the paper does not use.
- **Extension 2** uses compressed time (one "day" = 200 s) and assumed energy constants. Learned policies were trained on stress and evaluated on both regimes.
- **Not implemented:** the paper's DDPG/SAC/FD3QN/ensemble baselines, DKMS, CBS–D* Lite, and the CMDP safety extension (design only).

## 11. How to run everything

### Install (Python 3.11, CPU)
```
python3 -m venv .venv && . .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python -m pytest            # 68 tests, about 5 s
```

### Train (all checkpoints are already in `models/`)
```
python train_m7_ppo.py --timesteps 100000
python train_m8_masked_ppo.py --timesteps 100000
python train_m9_ccppo.py                                                  # full EdgePlus inner loop
python train_m9_ccppo.py --no-advisory --out models/m9_ccppo_noadv.pt
python train_m9_ccppo.py --no-ledger   --out models/m9_ccppo_noledger.pt
python train_m9_ccppo.py --no-masks    --out models/m9_ccppo_nomask.pt
python train_m9_ccppo.py --no-masks --no-advisory --no-ledger --out models/m9_ccppo_plain.pt
python train_m9_ccppo.py --no-advisory --no-ledger --out models/m9_ccppo_maskonly.pt
python train_m9_ccppo.py --set ledger.quarantine=false --out models/m9_ccppo_noquar.pt
python train_m9_ccppo.py --set reward.eta6=0 reward.eta7=0 --out models/m9_ccppo_noshape.pt
python train_m9_ccppo.py --set seeds.train_base=11000 --out models/m9_ccppo_s2.pt
python train_m9_ccppo.py --no-ledger --set seeds.train_base=11000 --out models/m9_ccppo_noledger_s2.pt
python train_m9_ccppo.py --set 'consensus.mode="mask_aware"' 'consensus.path="edge_cloud"' consensus.delay_scale=50 --out models/m9_ccppo_cons50.pt
python train_m9_ccppo.py --regime stress --no-ledger --set sensors.enabled=true sensors.lyapunov_weight=0.0 --out models/m9_ccppo_sens_l0.pt
python train_m9_ccppo.py --regime stress --no-ledger --set sensors.enabled=true sensors.lyapunov_weight=1.0 --out models/m9_ccppo_sens_l1.pt
```
Add `--smoke` to any script for a few-second pipeline check. A smoke run is not a result.

### Reproduce every table
| README section | Command | Output |
|---|---|---|
| 7.1 baselines | `python evaluate_baselines.py --regime {light,medium,stress}` | `results/baselines/<regime>/table.md` |
| 7.2 ablations | `python run_edgeplus.py --regime {medium,stress}` | `results/edgeplus/<regime>/` |
| 7.2 ungated PSO | `python run_edgeplus.py --regime stress --pso-ungated --only A1_full A2_no_pso` | `results/edgeplus/stress_pso_ungated/` |
| 7.3 PID | `python -m experiments.obj6_pid` | `results/obj6/` |
| 8.1 ledger follow-up | `python -m experiments.ledger_ablation --regime stress` | `results/ledger_ablation/stress/` |
| 8.2 consensus | `python run_consensus_extension.py --regime stress` and `... --policies ccppo_cons50` | `results/consensus/stress/` |
| 8.3 sensor energy | `python -m experiments.sensor_energy --regime {medium,stress}` | `results/sensor_energy/<regime>/` |

Each output folder has `summary.json` (per-seed and aggregate KPIs plus the git commit), `config.json`, and per-task / per-server CSVs (regenerated, not committed because of size).

## 12. Repository map
```
configs/base.json          every parameter; override any with dotted keys, e.g. "workload.regime"
env/                       simulator: edge_env.py (core), task_generator.py, server.py, sensors.py,
                           topology.py, ppo_env.py (Gym wrapper), factory.py, config.py
agents/                    baselines.py (random, greedy, Lyapunov greedy, SB3 wrappers),
                           ccppo.py (M9), sb3_train.py
advisory/                  nash.py, pid.py (PID, ZN, Jury, robustness), leader.py, layer.py
optimizer/pso.py           constricted PSO with SLA gate
ledger/                    ledger.py (blocks, PoA, BFT, reputation, debt), consensus.py (extension 1)
evaluation/                runner.py (paired evaluation), metrics.py, stats.py, report.py
diagnostics/feasibility.py why each task was or was not feasible
experiments/               presets.py, obj6_pid.py, ledger_ablation.py, sensor_energy.py
train_*.py, evaluate_baselines.py, run_edgeplus.py, run_consensus_extension.py   entry points
tests/                     68 pytest tests (simulator rules, ledger, advisory, PSO, CCPPO, sensors)
models/                    trained checkpoints with .json metadata and training curves
results/                   all tables and summaries
docs/assumptions.md        every assumption and deviation from the paper
reports/                   phase_a_audit.md, report_draft.md, m15_cmdp_design.md, energy_extension_notes.md
```

## 13. References
1. B. H. Taher, J. Luo, F. Ghrabat, Y. Qiao, "EdgePlus: A Multiagent Reinforcement Learning Framework for Dynamic Task Allocation in 6G Edge Computing," *IEEE Internet of Things Journal*, 13(8), 2026. DOI 10.1109/JIOT.2026.3656811.
2. Y. Mao, J. Zhang, K. B. Letaief, "Dynamic Computation Offloading for Mobile-Edge Computing with Energy Harvesting Devices" (LODCO, Lyapunov optimisation), [arXiv:1605.05488](https://arxiv.org/abs/1605.05488).
3. M. Min et al., "Learning-Based Computation Offloading for IoT Devices with Energy Harvesting," [arXiv:1712.08768](https://arxiv.org/abs/1712.08768).
4. L. Huang, S. Bi, Y. J. Zhang, "Deep Reinforcement Learning for Online Computation Offloading in Wireless Powered Mobile-Edge Computing Networks" (DROO), [arXiv:1808.01977](https://arxiv.org/abs/1808.01977).
5. J. Schulman et al., "Proximal Policy Optimization Algorithms," arXiv:1707.06347; M. Clerc and J. Kennedy, "The particle swarm: explosion, stability, and convergence," *IEEE TEC*, 2002.
