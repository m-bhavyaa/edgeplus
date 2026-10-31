# Phase A audit: EdgePlus reproduction

> **Status update (Phase B onward):** this audit describes the code at tag `preliminary-v0`. Defects D1–D20 were addressed in later commits, except D18 (Σk/f ≤ H; not implemented, see docs/assumptions.md #12). The §9 open decisions were resolved with documented defaults: paper deadline bands and shares; cloud fallback; recalibrated Poisson load; crypto, OBJ7 and CBS–D* out of scope; smoke and full run modes; all M14 options as ablations. The diagnostics script referenced in §3 was replaced by `diagnostics/feasibility.py` (current simulator); the CSVs in `results/audit/` came from the pre-audit code.

Date: 2026-10-31. Code audited: `main` at `cb22869`. No environment behaviour was changed in Phase A. The only additions are diagnostics, tests, and documents.

Evidence labels used below:
- **[run]**: verified by executing code in this sandbox.
- **[static]**: found by reading code only.
- **[paper]**: stated in Taher et al., IEEE IoT-J 13(8), 2026 (section or equation given).

---

## 1. Implementation inventory

| File | What it does | Status |
|---|---|---|
| `env/topology.py` | 10 cluster coordinates and hand-written adjacency | Works. Symmetric and connected **[run, tests/test_topology.py]** |
| `env/task.py` | `Task` dataclass. `deadline` is an absolute time; `deadline_slack` = deadline − arrival | Works |
| `env/task_generator.py` | Uniform arrivals on [0,100] s, uniform cluster, class shares 1/3 each, per-class uniform footprints | Works. Parameters differ from the paper (D7) |
| `env/server.py` | Server resources and an `active_jobs` list. Memory is held from assignment until finish | Works. `queue_time` is mislabelled (D2) |
| `env/edge_env.py` | 1669 lines. Lines 1–~1000 are two superseded `EdgePlusEnv` classes inside a string literal. The live class starts after that | Live class works. Dead code (D15) |
| `env/ppo_env.py` | Gymnasium wrapper: 125-dim observation, `Discrete(20)` actions, `action_masks()` | Works. Reset/obs issues (D8, D9) |
| `experiment-m6.py` | Random feasible baseline | Runs **[run]** |
| `train-m7-ppo.py`, `train-m8-maskedppo.py` | SB3 PPO / MaskablePPO, 50k steps, 500-task episodes, seed 42 | Not re-run (checkpoints exist) |
| `evaluate-m7.py` | Loads **`models/m8_masked_ppo`** with `PPO.load` | **Crashes [run]** (D1) |
| `evaluate-m8.py` | MaskablePPO evaluation, seed 100 | Runs and reproduces the recorded numbers **[run]** |
| `test.py`, `test-m3.py`, `test-m4-latency.py`, `test-m5.py` | Print-based scripts with no assertions. All of `test.py` is commented out except the last block | Run, but they verify nothing automatically |
| `models/*.zip` | M7 and M8 checkpoints | Load **[run]** |
| `env/__pycache__/*.pyc` | Committed bytecode (cpython-313) | Should be untracked |

The layout described in the brief (`test_topology.py`, `test_tasks.py`, ...) does not match the repository. The real script names use hyphens (`test-m3.py`, `experiment-m6.py`), so they cannot be imported as modules.

---

## 2. Reproduction of the recorded numbers [run]

All recorded M6/M7/M8 numbers reproduce exactly. See `results/preliminary/README.md`. The recorded M7 numbers come from the real `m7_ppo.zip` checkpoint, not from the M8 checkpoint that the current script points at.

---

## 3. Diagnosis of the 126 zero-feasible tasks and the 87.4 % M8 result [run]

Tool: `python -m diagnostics.feasibility_audit --policy {m8,random,m7} --seed 100`. Per-task CSVs and summaries are in `results/audit/`.

| Quantity (seed 100, 1000 tasks) | Random feasible | M8 masked PPO | M7 PPO |
|---|---|---|---|
| Zero-feasible tasks | 88 | 126 | 28 |
| ...of which URLLC / eMBB / mMTC | 81 / 7 / 0 | 104 / 22 / 0 | 28 / 0 / 0 |
| ...infeasible even on an idle server (static) | 28 | 28 | 28 |
| ...infeasible only because of queues (dynamic) | 60 | 98 | 0 |
| Primary reason (all zero-feasible tasks) | deadline | deadline | deadline |
| Mean routable servers failing memory, per zero-feasible task | 0.09 | 0.21 | 0.04 |
| Slice or energy rejections | 0 | 0 | 0 |
| Success given ≥1 feasible action | 100 % | 100 % | 27.1 % |
| Action marked feasible but failed | 0 | 0 | 0 |
| Mean feasible servers per task | 5.14 | 4.87 | 6.22 |
| Mean queue delay of chosen server* | 1.83 s | 4.40 s | n/a |
| Share of choices on the fast (2 GHz) server* | 63 % | 74 % | n/a |

\* Over tasks with at least one feasible server.

Findings:

1. **28 tasks are impossible by construction.** All are URLLC. The generator draws URLLC slack from U[1,5] s and CPU from U[1,4]·10⁹ cycles. The fastest server runs at 2 GHz, so processing alone can take 2 s. The paper's URLLC band is U[5,15] s (Sec. IV-B2), which would make all of these feasible.
2. **The remaining zero-feasible tasks are caused by congestion, and the policy affects it.** M8 places more work on fast servers and builds longer queues: 4.40 s mean queue delay against 1.83 s for random. Later URLLC tasks then find no server that can meet their deadline. M8 therefore has *more* zero-feasible tasks (126) than the random baseline (88).
3. **The M8 100 % conditional success follows from the code structure. It is not evidence of learning.** `execute()` re-runs the same `is_feasible()` checks on the same state that produced the mask. The simulator is deterministic and FIFO, and a newly admitted job is always appended *after* existing jobs, so an admitted job's completion time can never change afterwards. Under masking, "success" means "admitted", and success rate = 1 − zero-feasible rate. This is verified by `tests/test_invariants.py::test_masked_feasible_action_always_succeeds_and_vice_versa`.
4. **On the same evaluation workload, M8 (87.4 %) does worse than the random feasible policy (91.2 %).** The policy has learned to choose low-latency servers myopically. The reward is 10 − latency, so it never pays for the queueing it causes for later tasks. It also trained on a single replayed workload (D9) with unscaled inputs (D8) and an observation that omits the service class and reports absolute times as "queue" (D2).
5. The mask is computed for the current task before the action: `set_task` runs before `action_masks()`, and the diagnostic asserts that the mask equals the per-server checks. With an all-zero mask, MaskablePPO still returns an action. `execute()` then rejects it with reward −10 and `success=False`, so a missing action is never counted as a success. This handling is implicit and should be made explicit (D12).

**How the paper differs.** In the paper σ + violation = 100 % (for example 82.77 % + 17.23 % at 150k, Fig. 4). Every task is therefore executed, and a late task counts as a violation. Three properties of the paper avoid the tautology in finding 3: (a) a cloud fallback at the end of the routing order, so masks are non-empty for >99.9 % of tasks (Sec. IV-B5, step 5); (b) the deadline mask is hard only for URLLC "when safety gating is enabled" (Sec. IV-C5b); (c) admission uses a queue *surrogate* (Eq. 31), so realised latency can differ from the latency predicted when the mask was built. Our simulator has none of the three.

---

## 4. Paper-to-code mapping

Status key: **F** = faithfully reproduced · **A** = documented approximation · **N** = not implemented · **X** = extension beyond the paper · **U** = paper unclear or under-specified.

| Paper component | Formulation | Existing implementation | Missing pieces | Planned implementation |
|---|---|---|---|---|
| Clusters and neighbours (IV-C1) | C = 10 via weighted K-means; neighbours by Delaunay on centroids; 100 km² | Hand-placed 10-node grid with hand adjacency. **A** | No K-means, no Delaunay, no km scale | Keep the grid (the paper's data and centroids are unavailable). Optionally compute Delaunay adjacency on our coordinates. Document scale (1 unit = ? km). **U** |
| Server sets S = S^stat ∪ S^mob ∪ S^cloud (III-A) | Stationary and mobile servers per cluster; cloud c = 0 | 2 stationary servers per cluster, no mobile servers, no cloud. **N** for mobile and cloud | Mobile servers, cloud tier | Add server `kind` ∈ {stationary, mobile, cloud}. Counts and speeds are not in the paper, so they become configurable assumptions. **U** |
| Task tuple (t, d, c, p, k, m, b) (III-A) | as stated | Present. **F** (fields) | `tier`, `loc` are unused | Keep |
| Class shares (Table IV) | 20/50/30 % URLLC/eMBB/mMTC | 1/3 each. **mismatch** | | Configurable, default 20/50/30 |
| Deadlines (IV-B2) | URLLC U[5,15] s, eMBB U[30,120] s, mMTC U[120,600] s (relative to arrival) | U[1,5], U[5,15], U[10,30]. **mismatch** | | Paper bands as default; keep legacy bands as a named config |
| Footprints b, k, m (Alg. 3, step 5) | Derived from pollutant data (FootprintModel); no numeric ranges given | Uniform ranges. **A** | | Keep, documented as assumptions. **U** |
| Arrivals / load (Table IV) | 50k / 100k / 150k tasks per episode; arrival process from Brașov traces; horizon H unspecified | 1000 tasks uniform on [0,100] s. **A** | Load regimes | Poisson arrivals, rate calibrated so the "light" regime is near-unsaturated, then ×2 and ×3. Must be documented as calibration. **U** |
| Latency (Eq. 1) | L = L_tx + L_move + L_queue + L_proc | Same four terms. **A** | | Keep; fix timing (D3) |
| L_tx (Eq. 1, Eq. 30) | η_OH b / R̄; R̄ = ζ (W/Φ) log₂(1+SNR) η_MAC η_backhaul | b / (bandwidth·gain). **A** | Shannon rate, overhead | Implement Eq. 30 with configurable SNR, W, Φ, η terms (values unspecified). **U** |
| L_move | 0 for stationary/cloud; ‖x* − x_s‖ / v_s for mobile | 0.01 × cluster distance for any neighbour server. **mismatch** | | 0 for stationary; distance/speed for mobile; cloud → backhaul term |
| L_queue (Eq. 31) | Kingman-style surrogate ρ/(1−ρ)·(c_a²+c_s²)/2·E[S] | Exact FIFO backlog. **A** (arguably more precise) | Surrogate | Keep exact FIFO as the "ground truth" executor. Optionally add the surrogate as the *predicted* queue used by the mask, so predicted and realised latency can differ |
| L_proc (Eq. 32) | k / f_s | Same. **F** | | |
| Energy (Eq. 2) | E_tx = P·L_tx, E_move = χ‖Δx‖, E_comp = κ k | E = processing seconds × 1.0. **A** | | Implement Eq. 2 with configurable P, χ, κ. **U** |
| Routing order (III-C1, IV-C5b) | stationary in c(i) → mobile in c(i) → mobile in N(c(i)) → cloud | local + **all** neighbour servers, no order, no cloud. **mismatch** | | Implement candidate tiers. The paper does not say whether the order is a hard priority or only defines the candidate set; propose candidate set = union of the four tiers, with order exposed as a feature or tie-breaker. **U** |
| Per-server compute Σ k/f ≤ H (Eq. 3) | horizon budget | none. **N** | | Add, H configurable |
| Mobile energy Σ E ≤ E^max (Eq. 3) | mobiles only | energy budget on every server (never binds). **A** | | Apply to mobiles only, per Eq. 3 |
| Deadline t + L ≤ d (Eq. 3) | Hard for URLLC under safety gating (IV-C5b) | Hard for all classes. **mismatch** | | Configurable: `deadline_mask ∈ {all, urllc_only, none}` |
| Slice budgets (Eq. 4) | Per cluster, per class: Σ b/R̄ ≤ Γ^radio, Σ k/f ≤ Γ^compute (time budgets) | Per-server job-count cap of 10; the "global quota" is compared with a per-server count. **mismatch** (D4) | Cluster-level time budgets | Implement Eq. 4 over a sliding window H; Γ values unspecified. **U** |
| Objective J (Eq. 5) | α w 1[late] + β w L + γ E + δ 1[cloud] | none | | Metric only |
| Reward (Eq. 7) | +η₁w·1[on-time] − η₂w·1[late] − η₃L̃ − η₄Ẽ − η₅·1[cloud] | 10 − L or −10. **mismatch** | | Implement Eq. 7 with configurable η, w. Values unspecified. **U** |
| Masked MDP (III-E, Eq. 10) | π(a) = 0 if M = 0; masked softmax | MaskablePPO. **F** for single-agent masking | | |
| CCPPO (III-E, IV-E2) | Cooperative multi-actor {π_θj} with shared centralized critic V_ψ(s); actors use local obs at inference; GAE; clipped ratio; KL and entropy terms (Eq. 8); gradient clipping | none. **N** | Everything | See §6 |
| Advisory logits (Eq. 9) | z̃ = z + λ_N log s_c + λ_P u_c + λ_L 1[s = leader] | none. **N** | | Module `advisory/` |
| Nash sharing | best response on u_c = −α s·load − β energy − γ(s−1)², s ∈ [s_min, s_max], stop at ‖Δs‖∞ < ε | none. **N** | | As written. The symbol u_c is used for both Nash utility and PID output. **U** |
| PID (Eq. 11, 17, 39–40) | e = ρ_c − ρ_set; clipped u ∈ [−1,1]; ZN init; Jury test over ±20 % corners; FOPDT plant | none. **N** | | Implement PID, ZN tuning and Jury test; reproduce OBJ6 (cheap, no RL) |
| Leader election | score = ω₁(1 − load) + ω₂ energy; argmax per cluster | none. **N** | | As written |
| PSO (Eq. 12–13, IV-E4) | Particles = outer params Θ (inits/regularizers/advisory gains); inertia w_t linear decay **and** constriction k (φ > 4); SLA-gated acceptance (χ_cloud ≤ 0.07, fail ≤ 0.05, stationary ≥ 0.80, success improves); disabled at eval | none. **N** | | As written. Eq. 13b multiplies inertia by the constriction factor, which is unusual (standard Clerc constriction replaces inertia); implement as printed and flag it. P, I, c₁, c₂, w bounds unspecified. **U** |
| Reputation and debt (Eq. 14–16, 28–29) | ρ_rep = EMA(1[on-time] − κ·1[SLA viol.]); d_c = max(0, Θ̄ − Θ_c); reward −η₆φ(ρ) − η₇d; hinge φ with ρ_th = 0.6 (or softplus, β = 10); URLLC quarantine if ρ < ρ_th^URLLC | none. **N** | | `ledger/`. EMA rate, κ, η₆, η₇ unspecified. Θ_c is read as cluster throughput (Table V symbol). **U** |
| Edge PoA (Eq. 18–22) | log tuple per executed task (contains t_end and on-time flag); partial blocks; adaptive size S_c(t) (Eq. 21); SHA3-256 → BLAKE2b chain; median 0.39 ms | none. **N** | | Simulated ledger with real `hashlib` chaining; validation delay as a configurable distribution |
| Cloud BFT (Eq. 23–25) | periodic finalization; ascending cluster hashes; Ed25519 signature; median ≈ 6.9 ms; "off the critical path" | none. **N** | | Simulated rounds with a delay model; signatures modelled, not cryptographically implemented |
| Crypto, DKMS, attacks (III-M5–6, OBJ7) | X25519, AES-GCM, Ed25519, key rotation, attack injection | none | | **Proposed out of scope** (security evaluation). Ask the user |
| Mobility CBS–D* Lite (Alg. 4) | multi-agent path planning on a risk grid | none | | **Proposed approximation**: straight-line motion at v_s. Full CBS–D* Lite only if requested |
| Other schedulers (IV-D) | ensemble_ppo, fd3qn, ddpg, sac, ccppo_lagr | M6 random, M7 PPO, M8 MaskablePPO | | Not required by the brief; ccppo_lagr is relevant to M15 |
| Statistics (IV) | 5 episodes; 95 % CI; Wilcoxon signed-rank + Benjamini–Hochberg; seeds {38, 39, 40} | single run | | `evaluation/` with paired seeds |
| KPIs (Table V) | σ, violation, Lp50/p95 (all tasks), throughput, energy, LI, χ_cloud, URLLC tail, Jain fairness | success, latency over successes only | | Unified evaluator |
| Consensus-aware feasibility | not in paper | none | | **X** (M14). See §7 |
| CMDP safety | named as future work (VI-E) | none | | **X** (M15) |

---

## 5. Defects and inconsistencies (prioritised)

Severity: **P0** invalidates a reported result · **P1** a paper mismatch or modelling error that changes results · **P2** quality or reproducibility.

| ID | Sev | Defect | Evidence | Test |
|---|---|---|---|---|
| D1 | P0 | `evaluate-m7.py` loads the M8 checkpoint and crashes | [run] | `test_D1_*` (xfail) |
| D11 | P0 | With masking, success is identical to admission (tautology). M8's "100 % among feasible" holds by construction | [run] | `test_masked_feasible_action_always_succeeds_and_vice_versa` |
| D12 | P0 | No explicit outcome for zero-feasible tasks. M6 gives them reward 0 while M7/M8 give −10, so rewards are not comparable. M6 uses workload seed 42 (the training seed); M7/M8 use 100 | [static, run] | add in Phase B |
| D13 | P0 | Latency metrics cover successful tasks only and are not labelled. The paper's L_p50/p95 cover all executed tasks | [static] | add in Phase B |
| D3 | P1 | `start_time = now + queue` ignores L_tx + L_move: processing starts before the data arrives, so the server's `finish_time` is earlier than arrival + reported latency. The later queue estimates are biased in the same way | [run] | `test_D3_*` (xfail) |
| D2 | P1 | `Server.queue_time` returns the absolute last finish time and is fed to the policy as "queue". It grows with simulation time | [run] | `test_D2_*` (xfail) |
| D4 | P1 | The slice "global quota" is compared with a per-server count. There is no cluster-level budget, and Eq. 4's radio/compute *time* budgets are missing | [run] | `test_D4_*` (xfail) |
| D5 | P1 | No cloud tier, no mobile servers, no routing order. Stationary neighbour servers are allowed, but the paper only allows *mobile* neighbour servers | [static] | Phase B |
| D6 | P1 | Movement latency is applied to stationary neighbour servers (0.01 × grid distance, with unclear units) | [static] | Phase B |
| D7 | P1 | Deadline bands and class shares differ from the paper (Sec. IV-B2, Table IV) | [run] | `test_D7_*` (xfail ×2) |
| D8 | P1 | Observation values range up to ~1e9; no service-class feature; cluster encoded as a raw integer; no slice availability | [run] | `test_D8_*` (xfail) |
| D9 | P1 | `PPOEdgeEnv.reset()` regenerates the same seed-42 workload every episode, so training sees one 500-task trace | [run] | `test_D9_*` (xfail) |
| D10 | P1 | Energy = processing seconds; budget on every server; never binding (0 rejections) | [run] | Phase B |
| D14 | P1 | Reward is 10 − L / −10, not Eq. 7. It is myopic about the queueing it imposes on later tasks | [static] | Phase B |
| D16 | P1 | Deterministic executor: realised latency always equals predicted latency, so masks can never be "wrong". The paper predicts with a surrogate (Eq. 31). M14 needs a gap between predicted and realised latency to be meaningful | [static] | Phase B design |
| D17 | P2 | Memory is held from admission, including queue wait. Plausible, but undocumented | [static] | documented |
| D18 | P2 | No Σk/f ≤ H compute constraint (Eq. 3) | [static] | Phase B |
| D15 | P2 | ~1000 lines of dead code in a string in `edge_env.py`; `test.py` commented out; `.pyc` files committed; hyphenated script names; model paths depend on cwd | [static] | `test_D15_*` (xfail) |
| D19 | P2 | Server inventory duplicated in `ppo_env.py`, `experiment-m6.py` and the test scripts; no config file | [static] | Phase B |
| D20 | P2 | Unbounded `requirements.txt`; the README is missing | [static] | Phase B |

Checked and **not** defective [run]: topology symmetric, valid and connected; `reset()` clears jobs, energy and time; jobs are released at finish time; memory and energy never go negative; time cannot move backwards; the mask is built for the current task; an infeasible action changes no state; the generator is deterministic per seed.

---

## 6. Facts from the paper that shape M9–M14

- **CCPPO** (III-E, III-J, IV-E2): "cooperative multiactor policy", "cluster-aware actors", centralized critic V_ψ on global context, local observations at inference. The paper gives no number of actors, no parameter-sharing rule, no local-observation definition, and no joint-action format. Proposed approximation: one actor per cluster (A = 10). Each actor decides the tasks that arrive in its cluster, over a fixed action space of its candidate servers (local stationary, local mobile, neighbour mobile, cloud), with infeasible slots masked. Parameters are shared, with a cluster one-hot input, plus one centralized critic on the global state. Tasks arrive one at a time, so the joint action at a step is the action of the actor that owns the task, and all actors share the team reward. This is CTDE in the MAPPO style. It is labelled **A/U**, not "faithful".
- **Consensus timing** (III-M2, III-M3, VI-A): the log tuple contains t_end and the on-time flag, so PoA logging happens *after* execution. BFT is "off the critical path". The quoted delays are 0.39 ms (PoA) and 6.9 ms (BFT), against task deadlines of 5–600 s. Under the paper's own timing semantics, consensus does not delay task completion. With paper-calibrated delays, the effect of adding L_consensus to feasibility would be about 10⁻⁴ of the URLLC budget, which is likely unmeasurable.
- **PSO**: disabled at evaluation (IV-E4). The SLA gate is χ_cloud ≤ 0.07, fail ≤ 0.05, stationary ≥ 0.80.
- **Evaluation**: five episodes per regime, seeds {38, 39, 40}, Wilcoxon signed-rank with BH correction.

---

## 7. Implications for the M14 research question

Given §6, adding the paper's ledger delay to the mask would change almost nothing, and a positive result would be an artefact. For the extension to be scientifically honest, it must state a different, explicit transaction model. Proposed options, all configurable:

1. **Synchronous admission commit (extension assumption):** an assignment is dispatched only after the edge PoA commits an "assignment record". L_consensus = batching wait (block fill time, which follows from S_c(t) in Eq. 21 and the write rate) + validation time. Block fill time can reach tens to hundreds of ms under low write rates, which is far larger than 0.39 ms.
2. **Cross-cluster / cloud placements require BFT finality before dispatch:** add the BFT round period plus validation for those placements only.
3. **Delay sweep:** fixed, sampled (log-normal around the paper medians), load-dependent, and stress settings (for example 10–1000 ms) to find where consensus starts to matter.
4. **Prediction vs realisation:** the mask uses the *expected* consensus delay; the executor samples the realised delay, with timeouts. Without this gap, modes B and C in the brief are tautological for the same reason as D11.

All results must be reported over all offered tasks, with rejected / late / on-time counted separately.

---

## 8. Prioritised repair plan (Phase B)

Changes are made in order. Each step gets its own commit and test updates, and the xfail marker is removed when its defect is fixed.

1. **Evaluation integrity (D1, D11–D13):** a single `evaluation/` runner for M6/M7/M8 with identical workload seeds; explicit outcomes `on_time | late | rejected_no_feasible | rejected_infeasible_action`; latencies labelled "over executed tasks" and "over on-time tasks"; outcome-count validation; per-task CSV export.
2. **Configuration (D19, D20):** `configs/legacy.yaml` (current behaviour, kept for traceability) and `configs/paper_aligned.yaml`; one server-inventory builder.
3. **Timing fix (D3, D2):** start = max(now + L_tx + L_move, backlog end); expose relative backlog.
4. **Paper alignment (D5–D7, D10, D18, D4):** server kinds and routing order with cloud fallback; mobility as an approximation; deadline bands and class shares; Eq. 2 energy; Eq. 3 compute horizon; Eq. 4 cluster slice budgets; configurable deadline-mask scope.
5. **Prediction/realisation gap (D16):** stochastic service time and channel; mask uses expected values. Configurable, and off in `legacy`.
6. **RL interface (D8, D9, D14):** scaled observations with class one-hot and slice headroom; a new workload each episode with training seeds disjoint from evaluation seeds; Eq. 7 reward.
7. **Re-run M6/M7/M8** on the paper-aligned config with ≥5 paired seeds and store the results in `results/stabilized/`. Preliminary results stay untouched.

Then: M9 CCPPO → M10 advisory (PID/Jury and OBJ6 can be built in parallel because they need no RL) → M11 PSO → M12 ledger → M13 integration and ablations A1–A6 → M14 → M15 (design only unless time allows).

---

## 9. Open decisions (need the user's input)

1. **Paper-aligned defaults.** Adopting the paper's deadline bands and adding a cloud fallback will make the current 1000-task workload easy, so success will approach 100 %. Load must then be re-calibrated, with Poisson arrivals and light/medium/stress = 1×/2×/3× rate. Proposal: calibrate the light rate so the full-feasible random baseline stays below saturation, and do **not** tune it to match the paper's 82.77 %.
2. **Scope cuts:** proposal to exclude real cryptography, DKMS and attack injection (OBJ7), and to replace CBS–D* Lite with straight-line mobility. Both would be documented as limitations.
3. **Compute budget:** CPU-only sandbox. Proposal: smoke mode (≤2k tasks, ≤20k steps) and full mode (paper-scale loads scaled down by a stated factor, ≥5 seeds). Paper scale (150k tasks × 5 episodes × several configs) is likely hours per run on CPU.
4. **M14 transaction model:** choose among options 1–4 in §7, or approve all as ablations.
