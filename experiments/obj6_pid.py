"""OBJ6: PID robustness under +/-20 % gain drift (paper Sec. V-F, Figs. 15-17).

The paper does not give the FOPDT plant parameters. ASSUMPTION: K = 1, tau = 2 s,
L = 0.5 s, Ts = 0.1 s, 90 s horizon, |u| <= 100, feasibility = Ts <= 10 s and
Mp <= 15 % (the paper's criteria). Our numbers therefore are NOT comparable to
the paper's Ts = 2.74 s.

    python -m experiments.obj6_pid
Writes results/obj6/{summary.json, grid.csv}.
"""

from __future__ import annotations

import csv
import json

import numpy as np

from advisory.pid import robustness_check, ziegler_nichols_fopdt
from env.config import REPO_ROOT

PLANT = {"K": 1.0, "tau": 2.0, "L": 0.5, "Ts": 0.1}


def check(g):
    rows = robustness_check(*g, PLANT["K"], PLANT["tau"], PLANT["L"], PLANT["Ts"])
    return {"gains": [round(x, 4) for x in g], "corners_pass": sum(r["pass"] for r in rows[1:]),
            "nominal": rows[0], "worst_Ts": max(r["Ts"] for r in rows),
            "worst_Mp": max(r["Mp"] for r in rows)}


def certify(g, scale_all=False, max_iter=40):
    """Paper Alg. 2 lines 11-12: if any corner fails, reduce Kp and re-test.
    scale_all=True is OUR variant (not in the paper): shrink all three gains."""
    kp, ki, kd = g
    for it in range(max_iter):
        res = check((kp, ki, kd))
        if res["corners_pass"] == 8 and res["nominal"]["pass"]:
            return {"iterations": it, "certified": True, **res}
        kp *= 0.9
        if scale_all:
            ki, kd = ki * 0.9, kd * 0.9
    return {"iterations": max_iter, "certified": False, **res}


def main():
    out = REPO_ROOT / "results" / "obj6"
    out.mkdir(parents=True, exist_ok=True)
    zn = ziegler_nichols_fopdt(PLANT["K"], PLANT["tau"], PLANT["L"])
    summary = {"plant_assumption": PLANT, "zn_gains": check(zn), "paper_gains": check((1.9, 1.2, 0.06)),
               "zn_certified": certify(zn), "paper_certified": certify((1.9, 1.2, 0.06)),
               "zn_certified_scale_all": certify(zn, scale_all=True),
               "paper_certified_scale_all": certify((1.9, 1.2, 0.06), scale_all=True)}
    grid = []
    for kd in (0.04, 0.10, 0.16):
        for kp in np.linspace(1.5, 1.9, 9):
            for ki in np.linspace(0.9, 1.3, 9):
                r = check((kp, ki, kd))
                grid.append({"kp": kp, "ki": ki, "kd": kd, "pass_rate": r["corners_pass"] / 8,
                             "nominal_Ts": r["nominal"]["Ts"], "nominal_Mp": r["nominal"]["Mp"]})
    with (out / "grid.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(grid[0]))
        w.writeheader()
        w.writerows(grid)
    summary["grid_mean_pass_rate"] = float(np.mean([g["pass_rate"] for g in grid]))
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print(json.dumps({k: v for k, v in summary.items()}, indent=1, default=float)[:2500])


if __name__ == "__main__":
    main()
