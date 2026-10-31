# EdgePlus re-implementation with a consensus-delay-aware feasibility extension: report draft

Semester project. **Labels:** [PAPER] = numbers reported by Taher et al. (IEEE IoT-J 13(8), 2026); [OURS] = measured with this repository (commit given in each `summary.json`); [HYPOTHESIS] / [PENDING] as stated. Our simulator is a simplified stand-in for the paper's (see `docs/assumptions.md`), so **[OURS] numbers are not a reproduction of [PAPER] numbers**.

## 1. Abstract
We re-implement the main components of EdgePlus in a small Python simulator: feasibility-masked cooperative PPO (CCPPO) with a centralized critic, an advisory layer (Nash sharing, PID, leader election), a constricted-PSO outer loop, and a blockchain-lite ledger whose reputation and debt feed back into state, reward and masks. On 10 clusters with 31 servers and three synthetic load regimes, feasibility masks matter most [OURS]: removing them lowers on-time success by 17–26 pp at medium and stress load. The paper reports the same ordering, with smaller gaps. The advisory layer adds 1.0–2.1 pp. PSO under the paper's SLA gate never accepted a basin. We then test a proposed extension: an assignment must be committed by the ledger before dispatch, and the feasibility mask accounts for that delay. At paper-calibrated delays (sub-ms PoA) the extension makes no measurable difference. Only at 50× delays on the edge+cloud path does it give small gains: +1.1 pp for a greedy scheduler, and +0.7 pp for a CCPPO policy trained under that delay (seed-level p = 0.0625 each, the smallest attainable with 5 seeds).

## 2. Introduction and motivation
6G edge scheduling has hard per-task deadlines, per-slice budgets, and a need for tamper-evident logs. The paper's design idea is to make the feasible set explicit at sampling time and let learning optimise inside it. Our question extends this: if ledger confirmation sat on the dispatch path, should the feasibility check include it?

## 3. Problem formulation (as implemented)
- Task i = (t_i, d_i, c(i), p_i, k_i, m_i, b_i); servers are stationary, mobile, or cloud.
- Latency L = L_cons + L_tx + L_move + L_queue + L_proc (Eq. 1, plus L_cons for M14). Data is ready at t + L_cons + L_tx + L_move; FIFO start = max(ready, backlog end).
- Feasibility mask M_{i,s}: routing tier (stationary c(i) → mobile c(i) → mobile N(c(i)) → cloud), cluster slice compute budget (Eq. 4), memory, mobile energy (Eq. 3), deadline (URLLC only, Sec. IV-C5b), and URLLC reputation quarantine (Sec. III-H).
- Outcomes: on_time, late, rejected_no_feasible, rejected_infeasible_action. Success σ = on_time / offered; violation = 1 − σ (matching the paper's σ + viol = 100 %).
- Reward: Eq. 7 plus ledger shaping, Eq. 15.

## 4. EdgePlus baseline methodology: paper-to-code mapping

| Component | Paper | Code | Status |
|---|---|---|---|
| Routing order, slices, resources, deadline masks | III-C, IV-C5b | `env/edge_env.py` | Implemented. Slice budget compute part only |
| Latency / energy | Eq. 1–2, 30–32 | `env/edge_env.py` | Approximation (no Shannon rate, FIFO instead of Kingman surrogate) |
| Masked CCPPO, centralized critic | III-E, IV-E2, Eq. 8, 10 | `agents/ccppo.py` | Implemented to a documented spec: 10 parameter-shared cluster actors, local observations, global critic, GAE, clip, entropy, KL, gradient clipping |
| Advisory bias (Nash/PID/leader) | III-F, Eq. 9, 11 | `advisory/` | Implemented. Nash coupling and PID sign are our choices |
| PID ZN + Jury, ±20 % drift | III-I, V-F | `advisory/pid.py`, `experiments/obj6_pid.py` | Implemented. Plant parameters assumed |
| Constricted PSO, SLA gate | III-G, Eq. 13 | `optimizer/pso.py` | Implemented as printed; Θ = advisory gains only |
| Ledger: log tuple, partial blocks, hash chain, adaptive size, PoA, BFT, reputation, debt, quarantine | III-H, III-M, Eq. 14–29 | `ledger/ledger.py` | Simulated; no real cryptography |
| DKMS, AES-GCM, X25519, Ed25519, attack injection (OBJ7) | III-M5–6, V-G | n/a | Not implemented (out of scope) |
| CBS–D* Lite mobility | Alg. 4 | n/a | Replaced by straight-line travel |
| Baselines ensemble_ppo, fd3qn, ddpg, sac | IV-D | n/a | Not implemented. We use random, greedy, PPO, MaskablePPO instead |

All assumptions: `docs/assumptions.md`. The Phase A audit of the pre-existing code is in `reports/phase_a_audit.md`.

## 5. Implementation architecture
`env/` (simulator, workload, servers, Gym wrapper) · `agents/` (baselines, SB3 wrappers, CCPPO) · `advisory/` · `optimizer/` · `ledger/` · `evaluation/` (paired runner, KPIs, statistics, tables) · `diagnostics/` (per-task constraint breakdown) · `experiments/` (presets, OBJ6). Everything is configured in `configs/base.json` through dotted overrides.

## 6. Experimental setup [OURS]
- Regimes: light/medium/stress = 6/12/18 tasks/s over 200 s. Nominal capacity ≈ 16 tasks/s.
- Evaluation seeds 38–42, with identical workloads for every policy. Training seeds start at 10000; PSO seeds at 20000.
- Training on medium load: M7/M8 SB3 PPO 100k steps (55 s / 85 s CPU); CCPPO variants 60k steps (40–97 s CPU). This is a **small budget**; longer training may change the rankings.
- Reported: mean ± std over 5 seeds. Latency percentiles are over **executed** tasks only.

## 7. Baseline results (M6–M9) [OURS]
Source: `results/baselines/<regime>/table.md`. Simulator without ledger or advisory.

| Policy | Light σ % | Medium σ % | Stress σ % | Stress Lp95 exec (s) | Stress cloud % |
|---|---|---|---|---|---|
| M6 random feasible | 97.17 ± 0.57 | 94.59 ± 1.03 | 74.42 ± 0.90 | 62.19 | 25.0 |
| Greedy min predicted latency | 100.00 ± 0.00 | 99.92 ± 0.05 | 88.54 ± 4.54 | 19.51 | 13.0 |
| M7 PPO (unmasked) | 57.75 ± 0.75 | 35.43 ± 0.93 | 27.45 ± 0.37 | 33.91 | 98.7 |
| M8 MaskablePPO | 99.28 ± 0.36 | 98.12 ± 0.38 | 73.74 ± 1.02 | 31.72 | 17.8 |
| M9 CCPPO (masks only) | 99.48 ± 0.18 | 98.52 ± 0.25 | 74.18 ± 0.85 | 30.25 | 18.1 |

Observations:
1. Unmasked PPO (M7) collapses to sending almost everything to the cloud and loses 40–70 % of tasks to infeasible choices.
2. With masks, the learned policies beat random at light and medium load but **not** at stress (M8 −0.7 pp, M9 −0.2 pp vs random; seed-level p = 0.06 and 0.38).
3. A one-line greedy heuristic beats every learned policy at every load. With our training budget, the RL policies have not learned to exploit predicted-latency features as well as a direct argmin does. This is a limitation of our implementation, not a finding about EdgePlus.
4. M9 vs M8 (same masks, same simulator): within about 0.5 pp at every load.

**Zero-feasible handling.** At stress, 22.9 % of tasks (A1) have no feasible server: 52 % URLLC, 48 % eMBB. Primary reasons: memory 83 %, deadline 17 % (`diagnostics/feasibility.py`; every failed constraint is recorded per task). They are counted as violations. The paper's ">99.9 % non-empty masks" does not hold in our stress regime because we overload the system on purpose (rate 18 vs capacity ≈ 16).

## 8. Ablation study (A1–A6, Table VI) [OURS]
Source: `results/edgeplus/<regime>/table.md`.

| Config | Medium σ % | Stress σ % | Stress Lp95 (s) | Stress cloud % | Δσ vs A1 (stress) | [PAPER] stress σ % |
|---|---|---|---|---|---|---|
| A1 full | 99.48 ± 0.21 | 75.89 ± 1.26 | 29.47 | 22.3 | 0 | 82.8 |
| A2 no PSO | 99.48 ± 0.21 | 75.89 ± 1.26 | 29.47 | 22.3 | 0.00 | 82.0 |
| A3 no advisory | 98.49 ± 0.42 | 73.75 ± 0.88 | 34.29 | 18.2 | −2.14 (p = 0.06) | 80.0 |
| A4 no ledger | 99.39 ± 0.15 | 77.68 ± 0.98 | 27.08 | 17.6 | **+1.79** (p = 0.06) | 82.8 |
| A5 no masks | 73.97 ± 0.72 | 58.43 ± 1.16 | 28.04 | 34.9 | −17.46 (p = 0.06) | 77.3 |
| A6 plain CCPPO | 77.53 ± 0.36 | 58.56 ± 0.69 | 27.91 | 25.6 | −17.33 (p = 0.06) | 72.8 |

- **Masks dominate**, as in the paper, but our gaps (17 pp) are larger than the paper's (5.5–10 pp), because unmasked choices are rejected outright in our simulator.
- **Advisory helps** (+2.1 pp at stress, +1.0 pp at medium; 5/5 seeds in the same direction).
- **PSO under the paper's SLA gate was never accepted.** The best basins improved fitness (stress A1: 86.3 % → 92.1 % on PSO seeds), but cloud share (≈17 %) and failure (≈8 %) exceed the gate (≤ 7 %, ≤ 5 %), so A1 = A2. Extra ablation with the gate removed (`--pso-ungated`): A1 = 77.24 ± 1.32 % vs 75.89 % (+1.35 pp, seed p = 0.19), with Lp95 falling from 29.5 to 26.5 s.
- **Ledger feedback appeared to hurt at stress** (A4 better than A1 by 1.8 pp, 5/5 seeds). The follow-up below shows this is a **training-seed effect, not a ledger effect**.

**Follow-up: what drives the A4 > A1 gap?** (`python -m experiments.ledger_ablation --regime stress`, `results/ledger_ablation/stress/table.md`, success % over 5 eval seeds)

| Variant | What changes | Stress σ % |
|---|---|---|
| L1 full (= A2) | ledger on, quarantine on | 75.89 ± 1.26 |
| L2 | same model, quarantine off at evaluation only | 75.93 ± 1.26 |
| L3 | model trained and evaluated without quarantine | 75.80 ± 1.10 |
| L4 | model trained without reputation/debt reward shaping (η₆ = η₇ = 0) | 75.58 ± 1.03 |
| L5 ledger off (= A4) | no ledger in training or evaluation | 77.68 ± 0.98 |
| L6 | the L5 model evaluated **with** the ledger on | 77.70 ± 0.91 |
| L1, training seed 2 | ledger on, train_base = 11000 | 76.87 ± 0.66 |
| L5, training seed 2 | ledger off, train_base = 11000 | 76.08 ± 1.15 |

- Switching quarantine or shaping off changes success by at most 0.3 pp (L2–L4 vs L1), although quarantine restricted the options of 671 of 3667 URLLC tasks.
- The ledger-off model does just as well with the ledger switched on (L6 = L5). The gap therefore comes from *which network was trained*, not from what the ledger does at run time.
- With a second training seed the ordering flips: ledger on is 0.8 pp *better*. Averaged over both training seeds: ledger on 76.4 %, ledger off 76.9 % (−0.5 pp, within training-seed noise of about ±1 pp).
- **Conclusion [OURS]:** we find no measurable effect of ledger feedback on success at stress. A single training seed per model is not enough to rank configurations that differ by less than about 1–2 pp. This caveat applies to every A1–A4 comparison above.
- Ledger costs [OURS, seed 38 stress]: PoA validation median 0.10 ms (our size-scaled model; [PAPER] 0.39 ms); BFT median 7.1 ms ([PAPER] 6.9 ms; ours is configured from the paper's value, so this is not an independent check). 0 rejected blocks, 0 BFT timeouts.

## 9. OBJ6: PID robustness [OURS, assumed plant K = 1, τ = 2, L = 0.5, Ts = 0.1]
Source: `results/obj6/summary.json`.
- ZN gains (4.8, 4.8, 1.2): unstable or failing at all 8 drift corners (nominal Mp 116 %).
- Paper gains (1.9, 1.2, 0.06): nominal Ts 4.1 s, Mp 21.6 %; 2/8 corners pass. The paper's 2.74 s comes from a different, unknown plant.
- The paper's certification rule (reduce Kp only) did **not** certify either gain set in 40 steps on this plant. Our variant (shrink all gains by 10 % per step) certified the paper gains as (0.91, 0.57, 0.029) after 7 steps: all 8 corners pass, worst Ts 8.6 s, worst Mp 13.8 %. Starting from the ZN gains it overshot to a too-sluggish controller (Ts > 10 s) and did not certify.
- Mean ±20 % pass rate over the grid kp ∈ [1.5, 1.9], ki ∈ [0.9, 1.3], kd ∈ {0.04, 0.10, 0.16}: 43 %.

## 10. Consensus-delay-aware extension (M14) [EXTENSION, OURS]
**Timing semantics.** In the paper, the PoA log tuple is created after a task finishes, and BFT is off the critical path. Consensus therefore never delays a task, and adding the paper's delays to feasibility is a no-op by construction. We study a **hypothetical** transaction model: synchronous admission commit (`ledger/consensus.py`). Every assignment waits for its edge block to seal and validate. On the `edge_cloud` path, off-cluster placements also wait for the next BFT round. The mask uses the expected delay; execution samples the realised delay. `report_only` (mode C) adds the delay to latency only; `mask_aware` (mode B) also adds it to the deadline check.

**Results, stress load, 5 seeds** (`results/consensus/stress/table.md`). Each row gives σ % for report_only → mask_aware.

| Scenario | Mean L_cons (s) | CCPPO σ % | Greedy σ % | Greedy URLLC on-time % |
|---|---|---|---|---|
| No consensus (C0) | 0 | 75.89 | 88.54 | 54.4 |
| edge ×1 | 0.03 | 75.39 → 75.39 | 88.11 → 86.66 | 53.1 → 50.2 |
| edge ×10 | 0.25 | 75.83 → 75.83 | 87.57 → 88.19 | 51.7 → 52.9 |
| edge ×50 | 1.26 | 74.99 → 75.13 | 85.99 → 85.25 | 47.3 → 45.8 |
| edge+cloud ×1 | 0.10–0.15 | 75.17 → 75.17 | 87.89 → 88.49 | 53.5 → 54.5 |
| edge+cloud ×10 | 0.9–1.5 | 74.39 → 74.41 | 85.36 → 85.95 | 44.8 → 47.8 |
| edge+cloud ×50 | 3.9–5.2 | 65.96 → 65.94 | 67.98 → **69.04** (seed p = 0.0625) | 22.5 → 25.1 |
| BFT quorum broken (2/4 faulty) | 0.5–0.9 | 75.30 → 75.30 | 87.88 → 87.50 | 53.1 → 51.0 |

Interpretation:
- With paper-calibrated delays, consensus costs 0.4–0.7 pp of success (C0 vs report_only), and making the mask consensus-aware does not recover it.
- Mask-awareness only helps when consensus delay is a sizeable fraction of the URLLC budget (×50 on edge+cloud, mean 4–5 s against 5–15 s deadlines), and only for greedy: +1.06 pp success and +2.7 pp URLLC on-time. Its sign is inconsistent at smaller scales (−1.45 pp at edge ×1).
- The original CCPPO is almost unaffected because it was trained without consensus delay.
- **Consensus-trained CCPPO** (`m9_ccppo_cons50.pt`, trained in mask_aware edge+cloud ×50 mode; `results/consensus/stress/table_ccppo_cons50.md`). In its own training condition, mask-awareness now helps: σ 64.31 → 65.03 % (+0.72 pp) and URLLC on-time 23.1 → 25.5 % (+2.4 pp), with all 5 seeds in the same direction (seed p = 0.0625). In absolute terms it is **not** better than the original CCPPO in that condition (65.03 vs 65.96 %), and it is about 1.8 pp worse without consensus (74.14 vs 75.89 %). That is the cost of specialising to one delay setting, within the ≈1 pp training-seed noise found in §8. At paper-scale delays (×1) the two modes are again indistinguishable.
- **Threat to validity: per-task McNemar.** The pooled per-task McNemar p-values in the tables (e.g. 5e-17 for greedy at edge ×1) are not valid evidence. A tiny change in one decision changes the whole queue trajectory afterwards, so per-task outcomes are not independent paired samples. Only seed-level tests should be used, and with 5 seeds their smallest attainable p is 0.0625.
- **Answer to the research question [OURS]:** no evidence that consensus-aware feasibility improves deadline reliability at realistic (paper) delays. There is weak evidence (one configuration, one policy, p = 0.0625) of a small gain when synchronous BFT confirmation adds seconds of delay.

## 11. Limitations
Synthetic workload and topology; FIFO queue with an oracle backlog; no Shannon rate or path planning; no cryptography or attack experiments (OBJ7); small CPU training budgets with a single training seed per model; PSO only tunes advisory gains of a frozen policy, and its fitness uses short 1200-task episodes; 5 evaluation seeds; the paper's other baselines (ensemble PPO, FD3QN, DDPG, SAC) are not implemented; M15 is a design only (`reports/m15_cmdp_design.md`).

## 12. Conclusion and future work
The feasibility-first principle holds in our re-implementation: masks are the single largest factor. The advisory layer gives a small, consistent gain. PSO under the SLA gate did not help, and ledger feedback has no effect measurable beyond training-seed noise. The consensus-aware mask matters only when confirmation latency is on the dispatch path and reaches seconds. Next steps [PENDING]: multiple training seeds for every configuration (needed to resolve differences below about 1–2 pp); train under a range of consensus delays instead of one; implement M15 PPO-Lagrangian; per-sensor battery model (see `reports/energy_extension_notes.md`).
