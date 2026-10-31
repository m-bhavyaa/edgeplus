# Assumptions and deviations from the paper

The paper (Taher et al., IEEE IoT-J 13(8), 2026) leaves many implementation details open. This table lists every value or modelling choice we had to make, where it is configured, and how it might affect results. Anything not listed here follows the paper as cited in the code docstrings.

| # | Topic | Paper says | Our choice | Where | Likely effect |
|---|---|---|---|---|---|
| 1 | Topology | 10 clusters via weighted K-means on Brașov sites, Delaunay neighbours, 100 km² | Hand-placed 10-node grid with fixed adjacency; 1 grid unit = 1 km | `env/topology.py`, `servers.km_per_grid_unit` | Cluster distances drive mobile travel times |
| 2 | Workload source | Brașov air-quality traces → tasks (Alg. 3) | Synthetic: Poisson arrivals, uniform home cluster, uniform footprints per class | `workload.*` | Arrivals are less bursty than real traces, so queues are likely milder |
| 3 | Load regimes | 50k/100k/150k tasks, horizon not given | 6/12/18 tasks/s over 200 s (1200/2400/3600 tasks); edge+cloud capacity ≈ 16 tasks/s | `workload.load_regimes_tasks_per_s` | Absolute success rates are not comparable with the paper |
| 4 | Footprints (k, m, b) | Derived by FootprintModel, no ranges given | Uniform ranges carried over from the pre-audit code | `workload.cpu_cycles` etc. | Sets how hard deadlines are |
| 5 | Server inventory | stationary + mobile per cluster + cloud; counts and speeds not given | 2 stationary (1 and 2 GHz), 1 mobile (1.5 GHz, 33.3 m/s = 120 km/h), 1 cloud (10 GHz, 0.5 s backhaul) | `servers.*` | |
| 6 | Mobility | CBS–D* Lite on a risk grid | Straight-line travel at constant speed; mobiles do not relocate | `EdgePlusEnv.movement_latency` | Neighbour mobiles are slow (≈60 s), so in practice they serve only eMBB/mMTC |
| 7 | Rate model | Eq. 30 (Shannon with ζ, Φ, η factors) | bandwidth × channel gain | `transmission_latency` | No SNR dynamics |
| 8 | Queue model | Kingman surrogate (Eq. 31) | Exact FIFO backlog; the mask uses expected k/f, execution uses k/f × slowdown × LogNormal(cv = 0.25) | `simulator.service_noise_cv` | Gives a gap between predicted and realised latency, so admitted tasks can be late. The scheduler sees the true backlog of queued jobs (oracle) |
| 9 | Degraded servers | none (reputation needs misbehaviour) | Servers 3 and 12 run 1.8× slower | `servers.degraded_servers` | Gives the reputation signal something to detect |
| 10 | Energy | Eq. 2 with P, χ, κ unspecified | P_tx = 0.5 W, χ = 0.01 J/m, κ = 1e-9 J/cycle; budget (3000 J) on mobiles only | `simulator.energy` | Energy is rarely binding |
| 11 | Slice budgets Γ | Eq. 4, values not given | Compute part only: outstanding processing seconds per cluster and class ≤ {URLLC 20, eMBB 80, mMTC 20}; radio part not modelled; cloud has no slice | `simulator.slice_compute_budget_s` | |
| 12 | Σ k/f ≤ H (Eq. 3) | per-server horizon budget | Not implemented (implied by queueing) | | |
| 13 | Deadline mask scope | hard for URLLC "when safety gating is enabled" | Default `urllc`; `all` and `none` also available | `simulator.deadline_mask` | eMBB/mMTC can be admitted and then run late |
| 14 | Zero-feasible tasks | paper reports masks non-empty for >99.9 % of tasks | Rejected explicitly (`rejected_no_feasible`), counted as a violation | `EdgePlusEnv.reject` | |
| 15 | Reward Eq. 7 | η₁…η₅, w_p unspecified | η = (1, 1, 0.2, 0.05, 0.2), w = (3, 2, 1); latency normalised by the deadline budget; extra −2 for an infeasible action | `reward.*` | |
| 16 | Ledger shaping | η₆, η₇, κ, EMA rate unspecified | η₆ = 0.5, η₇ = 0.2, κ = 0.5, α = 0.1, ρ_th = 0.6, URLLC quarantine below 0.65 | `ledger.*` | |
| 17 | Debt d_c | max(0, Θ̄ − Θ_c) | Normalised by Θ̄; Θ_c = committed on-time completions per second | `Ledger.debt` | |
| 18 | PoA / BFT | 0.39 ms PoA median; BFT 6.9 ms median, periodic | LogNormal delays with those medians; BFT every 1 s with n = 4 replicas; Ed25519/AES/X25519 not implemented (hash stand-ins) | `ledger.*` | No real cryptography; OBJ7 security experiments are out of scope |
| 19 | CCPPO agents | "cluster-aware actors", centralized critic | 10 actors with shared parameters and a cluster one-hot; K = 8 candidate slots; one centralized critic on global state; team reward | `agents/ccppo.py` | See report §4 |
| 20 | Advisory signs | Eq. 9 adds λ_P·u_c | We use −λ_P·u_c, so overloaded clusters become less attractive | `advisory/layer.py` | |
| 21 | Nash coupling | not given | Spill-over of neighbour load in proportion to relative share (coupling 0.3); 41-point grid best response | `advisory/nash.py` | The β·energy term is constant in s_c, as printed |
| 22 | PSO Θ | inits/regularizers/advisory gains | Advisory gains only, on a frozen policy (pre-tune mode); 6 particles × 4 iterations; fitness on 2 PSO-only seeds × 1200 tasks | `optimizer/pso.py`, `run_edgeplus.py` | Fitness episodes are shorter than evaluation episodes |
| 23 | PSO update | Eq. 13b uses inertia w_t AND constriction k | Implemented as printed (non-standard) | `optimizer/pso.py` | |
| 24 | PID plant (OBJ6) | FOPDT, parameters not given | K = 1, τ = 2 s, L = 0.5 s, Ts = 0.1 s | `experiments/obj6_pid.py` | Our Ts/Mp values are not comparable with Table VII |
| 25 | Consensus on the critical path (M14) | none: logging after execution, BFT off the critical path | EXTENSION: synchronous admission commit; batching wait U(0, min(T_block, S_c/λ_c)) + PoA; off-cluster placements also wait for the next BFT round (edge_cloud path); broken quorum → 3 retries counted as confirmation failures | `ledger/consensus.py` | This is a hypothetical transaction model. It is not a property of EdgePlus |
| 26 | Statistics | 5 episodes, Wilcoxon + BH | 5 seeds {38–42}; exact paired sign-flip permutation (minimum two-sided p = 0.0625 with 5 seeds); pooled per-task McNemar shown but NOT valid as an independent test (see report §10) | `evaluation/stats.py` | |
| 27 | Training seeds | not given | Training workloads from seeds 10000+, PSO from 20000+, evaluation 38–42 (disjoint) | `seeds.*` | |
