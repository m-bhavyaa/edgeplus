# M15: constrained-MDP safety extension (design only, NOT implemented)

Status: not implemented and not tested. We have no results for it. The paper names "formal CMDP safety" as future work (Sec. VI-E).

## Objective and constraints
maximise   E[Σ_t γ^t r_t]          (Eq. 7 reward without the lateness penalty)
subject to E[Σ_t γ^t c^dl_t] ≤ d_dl     c^dl_t = 1[task t misses its deadline or is rejected]
           E[Σ_t γ^t c^E_t]  ≤ d_E      c^E_t  = energy of the assignment / E_ref
           (optional) E[c^to_t] ≤ d_to  c^to_t = 1[consensus confirmation failure]

## Method: PPO-Lagrangian on top of CCPPO
- Keep the CCPPO actor and add one cost critic V_c^j(s) per constraint, trained like the value critic.
- Advantage: Â_t = Â^r_t − Σ_j λ_j Â^{c_j}_t, using GAE for each signal.
- Dual update after each PPO update: λ_j ← max(0, λ_j + η_λ (Ĵ_{c_j} − d_j)), where Ĵ is the episode cost.
- The masks stay. The CMDP handles constraints the mask cannot evaluate at decision time: realised lateness under service noise, and the long-run energy budget.

## How it differs from masked PPO
A mask removes actions predicted to be infeasible **now**. It cannot express expected long-run budgets or risk caused by noise. The Lagrangian learns a price on those costs. The paper's `ccppo_lagr` baseline is this method **without** masks.

## Planned comparison
Masked CCPPO (A4 config) vs masked CCPPO-Lagrangian vs unmasked CCPPO-Lagrangian, on the same 5 evaluation seeds. Reported: success, deadline-cost rate vs d_dl, energy vs d_E, and the λ trajectories.
