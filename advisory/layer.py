"""Advisory layer: combines Nash, PID, and leader into a logit bias (Eq. 9).

    z~_s = z_s + lambda_N log s_c(s) - lambda_P u_c(s) + lambda_L 1[s = leader_c(s)]

The bias is added to the policy's logits BEFORE masking, so infeasible actions
stay at probability 0 (Eq. 10): the advisory layer can only reorder feasible
servers. The cloud (cluster -1) gets zero bias.
"""

from __future__ import annotations

import numpy as np

from .leader import elect_leaders
from .nash import nash_shares
from .pid import PID


class AdvisoryLayer:

    def __init__(self, cfg: dict, num_clusters: int):
        self.cfg = cfg
        self.C = num_clusters
        self.set_gains(cfg["lambda_n"], cfg["lambda_p"], cfg["lambda_l"])
        self.reset()

    def set_gains(self, lam_n: float, lam_p: float, lam_l: float) -> None:
        """Used by the PSO outer loop (M11)."""
        self.lam = (float(lam_n), float(lam_p), float(lam_l))

    def reset(self) -> None:
        p = self.cfg["pid"]
        self.pids = [PID(p["kp"], p["ki"], p["kd"], p["dt"]) for _ in range(self.C)]
        self.u = np.zeros(self.C)
        self.next_tick = 0.0
        self.last_shares = np.ones(self.C)
        self.last_iters = 0

    def _update_pid(self, core, rho) -> None:
        while core.time >= self.next_tick:          # PID runs at fixed sim-time steps
            e = rho - self.cfg["pid"]["rho_set"]
            self.u = np.array([self.pids[c].step(e[c]) for c in range(self.C)])
            self.next_tick += self.cfg["pid"]["dt"]

    def bias(self, core) -> np.ndarray:
        """Bias vector over ALL servers for the current state."""
        rho = np.array([core.cluster_load(c) for c in range(self.C)])
        energy = np.array([np.mean([s.energy_used for s in core.servers if s.cluster == c])
                           for c in range(self.C)])
        shares, self.last_iters = nash_shares(rho, energy, core.topology.neighbors, self.cfg["nash"])
        self.last_shares = shares
        self._update_pid(core, rho)
        leaders = elect_leaders(core, self.cfg["leader"]["w1"], self.cfg["leader"]["w2"])
        lam_n, lam_p, lam_l = self.lam
        b = np.zeros(len(core.servers))
        for s in core.servers:
            c = s.cluster
            if c < 0:
                continue
            b[s.id] = lam_n * np.log(shares[c]) - lam_p * self.u[c] \
                + lam_l * float(leaders.get(c) == s.id)
        return b


def masked_probs(logits: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Eq. 10 masked softmax; raises if the mask is empty (caller must reject)."""
    if not mask.any():
        raise ValueError("empty mask: task must be rejected explicitly")
    z = np.where(mask, logits, -np.inf)
    z = z - z[mask].max()
    p = np.exp(z)
    return p / p.sum()
