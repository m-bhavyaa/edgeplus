"""Evaluate M6 (random feasible), greedy, M7 (PPO) and M8 (MaskablePPO) on the
same paired workloads.

    python evaluate_baselines.py --regime medium            # full: 5 seeds, full episodes
    python evaluate_baselines.py --regime medium --smoke    # 2 seeds x 300 tasks
Writes results/baselines/<regime>/<policy>/{tasks_seed*.csv, summary.json} and table.md.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from agents.baselines import GreedyMinLatency, RandomFeasible, SB3Policy
from env.config import REPO_ROOT, load_config
from evaluation.report import table
from evaluation.runner import evaluate
from experiments.presets import BASELINE


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regime", default="medium")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "results" / "baselines")
    a = ap.parse_args()
    cfg = load_config(overrides={**BASELINE, "workload.regime": a.regime})
    seeds = cfg["seeds"]["eval"][:2] if a.smoke else cfg["seeds"]["eval"]
    n = 300 if a.smoke else None
    out = a.out / (a.regime + ("_smoke" if a.smoke else ""))
    policies = [RandomFeasible(seed=0), GreedyMinLatency()]
    for fname, masked, name in (("m7_ppo", False, "m7_ppo"), ("m8_masked_ppo", True, "m8_masked_ppo")):
        path = REPO_ROOT / "models" / f"{fname}.zip"
        if path.exists():
            policies.append(SB3Policy(str(path), masked, name))
        else:
            print(f"[skip] {path} not found; train it first")
    m9 = REPO_ROOT / "models" / "m9_ccppo_maskonly.pt"     # CCPPO, masks only (no advisory/ledger)
    if m9.exists():
        from agents.ccppo import CCPPO
        policies.append(CCPPO.load(m9, cfg, name="m9_ccppo_maskonly"))
    sums = [evaluate(p, cfg, p.name, out, seeds, n) for p in policies]
    md = (f"Regime **{a.regime}**, seeds {seeds}, tasks/episode "
          f"{n or 'full'}. Mean ± std across seeds. p-values vs m6_random.\n\n"
          + table(sums, ref="m6_random"))
    (out / "table.md").write_text(md + "\n")
    print(md)


if __name__ == "__main__":
    main()
