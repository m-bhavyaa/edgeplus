"""M13: integrated EdgePlus-style evaluation with ablations A1-A6 (paper Table VI).

Pipeline per ablation (follows Alg. 1/2): load the CCPPO policy trained with the
matching components -> optional PSO pre-tune of advisory gains on PSO-only
workloads (SLA-gated) -> freeze -> evaluate on the paired evaluation seeds.

    python run_edgeplus.py --regime stress            # all ablations, 5 seeds
    python run_edgeplus.py --regime medium --smoke    # 2 seeds x 400 tasks, small PSO

Models expected (train with train_m9_ccppo.py, see README):
    m9_ccppo.pt (masks+adv+ledger) m9_ccppo_noadv.pt m9_ccppo_noledger.pt
    m9_ccppo_nomask.pt m9_ccppo_plain.pt
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from agents.ccppo import CCPPO
from env.config import REPO_ROOT, load_config
from evaluation.report import table
from evaluation.runner import evaluate, run_episode
from evaluation.metrics import summarize
from experiments.presets import ABLATIONS
from optimizer import ConstrictedPSO

MODEL_FOR = {  # (masks, advisory, ledger) -> checkpoint
    (True, True, True): "m9_ccppo.pt", (True, False, True): "m9_ccppo_noadv.pt",
    (True, True, False): "m9_ccppo_noledger.pt", (False, True, True): "m9_ccppo_nomask.pt",
    (False, False, False): "m9_ccppo_plain.pt",
}


def ablation_cfg(flags: dict, regime: str) -> dict:
    return load_config(overrides={"workload.regime": regime, "ledger.enabled": flags["ledger"],
                                  "advisory.enabled": flags["advisory"], "consensus.mode": "off"})


def pso_pretune(policy: CCPPO, cfg: dict, n_tasks: int, n_seeds: int, small: bool) -> dict:
    """Tune (lambda_N, lambda_P, lambda_L) on PSO-only seeds (disjoint from eval seeds)."""
    p = dict(cfg["pso"])
    if small:
        p.update(particles=3, iterations=1)
    seeds = [cfg["seeds"]["pso_base"] + i for i in range(n_seeds)]

    def fitness(x):
        policy.advisory.set_gains(*x)
        ms = [summarize(run_episode(policy, cfg, s, n_tasks)[0], cfg["workload"]["horizon_s"])
              for s in seeds]
        return {k: float(np.mean([m[k] for m in ms])) for k in ms[0] if isinstance(ms[0][k], float)}

    inc = np.array(policy.advisory.lam)
    out = ConstrictedPSO(p, seed=cfg["seeds"]["pso_base"]).run(fitness, inc)
    policy.advisory.set_gains(*out["adopted"])     # frozen from here on (PSO off at eval)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regime", default="stress")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--only", nargs="*", help="subset of ablation names")
    ap.add_argument("--pso-ungated", action="store_true",
                    help="EXTRA ablation (not in paper): accept any PSO basin that improves success")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "results" / "edgeplus")
    a = ap.parse_args()
    out = a.out / (a.regime + ("_smoke" if a.smoke else "") + ("_pso_ungated" if a.pso_ungated else ""))
    out.mkdir(parents=True, exist_ok=True)
    sums, pso_logs = [], {}
    for name, flags in ABLATIONS.items():
        if a.only and name not in a.only:
            continue
        cfg = ablation_cfg(flags, a.regime)
        if a.pso_ungated:
            cfg["pso"]["sla"] = {"max_cloud": 1.0, "max_fail": 1.0, "min_stationary": 0.0}
        seeds = cfg["seeds"]["eval"][:2] if a.smoke else cfg["seeds"]["eval"]
        n = 400 if a.smoke else None
        ck = REPO_ROOT / "models" / MODEL_FOR[(flags["masks"], flags["advisory"], flags["ledger"])]
        pol = CCPPO.load(ck, cfg, name=name)
        if flags["pso"] and pol.advisory is not None:
            pso_logs[name] = pso_pretune(pol, cfg, 400 if a.smoke else 1200, 1 if a.smoke else 2,
                                         small=a.smoke)
            print(name, "PSO accepted:", pso_logs[name]["accepted"], "gains:", pso_logs[name]["adopted"])
        sums.append(evaluate(pol, cfg, name, out, seeds, n))
    (out / "pso.json").write_text(json.dumps(pso_logs, indent=2))
    md = (f"Regime **{a.regime}**, seeds {sums[0]['seeds']}, tasks/episode "
          f"{sums[0]['num_tasks'] or 'full'}. Mean ± std across seeds. p-values vs A1.\n\n"
          + table(sums, ref="A1_full" if any(s["name"] == "A1_full" for s in sums) else None))
    (out / "table.md").write_text(md + "\n")
    print(md)


if __name__ == "__main__":
    main()
