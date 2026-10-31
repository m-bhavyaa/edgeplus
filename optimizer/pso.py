"""M11: constricted PSO outer loop (paper Eq. 12-13, Sec. III-G, IV-E4).

Implemented exactly as printed:
    w_t   = w_max - (w_max - w_min) * t / I                               (13a)
    v_t+1 = k*w_t*v_t + k*c1*r1*(p - x_t) + k*c2*r2*(g - x_t)             (13b)
    x_t+1 = x_t + v_t+1                                                   (13c)
    k     = 2 / |2 - phi - sqrt(phi^2 - 4 phi)|,  phi = c1 + c2 > 4       (13d)
Note: (13b) combines a decaying inertia w_t WITH Clerc's constriction k. Standard
constricted PSO uses k alone; we follow the paper and flag this in the docs.

Boundary handling (not in the paper, ASSUMPTION): positions are clipped to the
box and the velocity component that hit the wall is set to zero.

SLA-gated acceptance (Sec. III-G): the best basin is adopted only if its success
beats the incumbent AND cloud share <= 0.07, failure <= 0.05, stationary >= 0.80.

Scope (ASSUMPTION): the paper's Theta covers "inits/regularizers/advisory gains".
We optimise only the advisory gains (lambda_N, lambda_P, lambda_L) of a FROZEN
CCPPO policy (pre-tune mode); network weights are not perturbed. PSO is never
run during evaluation.
"""

from __future__ import annotations

import math
from typing import Callable

import numpy as np


def constriction(c1: float, c2: float) -> float:
    phi = c1 + c2
    if phi <= 4:
        raise ValueError("constriction requires phi = c1 + c2 > 4")
    return 2.0 / abs(2.0 - phi - math.sqrt(phi * phi - 4.0 * phi))


def sla_ok(m: dict, sla: dict) -> bool:
    return (m["cloud_share_exec"] <= sla["max_cloud"] and m["violation_all"] <= sla["max_fail"]
            and m["stationary_share_exec"] >= sla["min_stationary"])


class ConstrictedPSO:

    def __init__(self, p: dict, seed: int):
        self.p = p
        self.rng = np.random.default_rng(seed)
        self.k = constriction(p["c1"], p["c2"])
        self.lo, self.hi = np.array(p["bounds"], float).T

    def run(self, fitness: Callable[[np.ndarray], dict], incumbent: np.ndarray) -> dict:
        """fitness(x) -> metrics dict with 'success_all' etc. Returns the history and
        the accepted position (incumbent if no basin passes the SLA gate)."""
        P, I, p = self.p["particles"], self.p["iterations"], self.p
        dim = len(self.lo)
        x = self.rng.uniform(self.lo, self.hi, (P, dim))
        x[0] = incumbent                                    # warm start one particle
        v = np.zeros((P, dim))
        evals = [fitness(xi) for xi in x]
        pbest, pbest_f = x.copy(), np.array([e["success_all"] for e in evals])
        g = pbest[pbest_f.argmax()].copy()
        history = [{"iter": 0, "x": xi.tolist(), **_brief(e)} for xi, e in zip(x, evals)]
        base = evals[0]
        for t in range(1, I + 1):
            w = p["w_max"] - (p["w_max"] - p["w_min"]) * t / I
            r1, r2 = self.rng.random((P, dim)), self.rng.random((P, dim))
            v = self.k * w * v + self.k * p["c1"] * r1 * (pbest - x) + self.k * p["c2"] * r2 * (g - x)
            x = x + v
            hit = (x < self.lo) | (x > self.hi)
            x, v[hit] = np.clip(x, self.lo, self.hi), 0.0
            for i in range(P):
                e = fitness(x[i])
                history.append({"iter": t, "x": x[i].tolist(), **_brief(e)})
                if e["success_all"] > pbest_f[i]:
                    pbest[i], pbest_f[i] = x[i].copy(), e["success_all"]
            g = pbest[pbest_f.argmax()].copy()
        best = fitness(g)
        accepted = best["success_all"] > base["success_all"] and sla_ok(best, p["sla"])
        return {"k": self.k, "history": history, "incumbent": incumbent.tolist(),
                "incumbent_metrics": _brief(base), "best": g.tolist(), "best_metrics": _brief(best),
                "sla_ok": sla_ok(best, p["sla"]), "accepted": bool(accepted),
                "adopted": (g if accepted else incumbent).tolist()}


def _brief(m: dict) -> dict:
    return {k: float(m[k]) for k in ("success_all", "violation_all", "cloud_share_exec",
                                     "stationary_share_exec", "lat_p95_exec")}
