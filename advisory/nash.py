"""Nash resource sharing (paper Sec. III-F).

Each cluster c picks a sharing factor s_c in [s_min, s_max] by best response to
    u_c(s_c) = -alpha * s_c * load_c(s) - beta * energy_c - gamma * (s_c - 1)^2
and iterates until ||s(t+1) - s(t)||_inf < eps.

ASSUMPTION (paper gives no coupling): clusters interact through load. Cluster c
absorbs part of each neighbour's load in proportion to its relative share:
    load_c(s) = rho_c + coupling * mean_{n in N(c)} [ s_c / (s_c + s_n) * rho_n ]
Note: the beta*energy_c term is constant in s_c as printed, so it does not
change the best response; it is kept for fidelity to the equation.
The output enters the logits as lambda_N * log(s_c)  (Eq. 9).
"""

from __future__ import annotations

import numpy as np


def nash_shares(rho: np.ndarray, energy: np.ndarray, neighbors: dict, p: dict) -> tuple:
    """Return (shares, iterations). Best response is found on a 41-point grid."""
    grid = np.linspace(p["s_min"], p["s_max"], 41)
    s = np.ones(len(rho))
    for it in range(1, p["max_iter"] + 1):
        new = s.copy()
        for c in range(len(rho)):
            ns = neighbors[c]
            spill = np.mean([grid / (grid + s[n]) * rho[n] for n in ns], axis=0) if ns else 0.0
            load = rho[c] + p["coupling"] * spill
            u = -p["alpha"] * grid * load - p["beta"] * energy[c] - p["gamma"] * (grid - 1) ** 2
            new[c] = grid[int(np.argmax(u))]
        done = np.max(np.abs(new - s)) < p["eps"]
        s = new
        if done:
            return s, it
    return s, p["max_iter"]
