"""Why does ledger feedback hurt at stress? (follow-up to report section 8, A4 > A1)

The ledger touches the scheduler in three ways (paper Sec. III-H):
  (a) URLLC quarantine in the mask, (b) reward shaping -eta6*phi(rho) - eta7*d,
  (c) reputation feature in the observation.
This runs them separately on the same 5 evaluation seeds (no PSO, advisory on):

  L1_full            model m9_ccppo.pt,          ledger on, quarantine on    (= A2)
  L2_noquar_eval     model m9_ccppo.pt,          quarantine switched off at evaluation only
  L3_noquar_trained  model m9_ccppo_noquar.pt,   quarantine off in training and evaluation
  L4_noshape         model m9_ccppo_noshape.pt,  eta6 = eta7 = 0 in training, quarantine on
  L5_ledger_off      model m9_ccppo_noledger.pt, ledger disabled              (= A4)
  *_seed2            same as L1 / L5 but trained with seeds.train_base = 11000
  L6_offmodel_ledger_on  the L5 model evaluated with the ledger switched on

    python -m experiments.ledger_ablation --regime stress
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

import numpy as np

from agents.ccppo import CCPPO
from env.config import REPO_ROOT, load_config
from evaluation.report import table
from evaluation.runner import evaluate

VARIANTS = {
    "L1_full": ("m9_ccppo.pt", {}),
    "L2_noquar_eval": ("m9_ccppo.pt", {"ledger.quarantine": False}),
    "L3_noquar_trained": ("m9_ccppo_noquar.pt", {"ledger.quarantine": False}),
    "L4_noshape": ("m9_ccppo_noshape.pt", {"reward.eta6": 0.0, "reward.eta7": 0.0}),
    "L5_ledger_off": ("m9_ccppo_noledger.pt", {"ledger.enabled": False}),
    # second training seed (seeds.train_base = 11000) to measure training-seed variance
    "L1_full_seed2": ("m9_ccppo_s2.pt", {}),
    "L5_ledger_off_seed2": ("m9_ccppo_noledger_s2.pt", {"ledger.enabled": False}),
    # ledger-off model evaluated WITH the ledger on (its reputation input now varies)
    "L6_offmodel_ledger_on": ("m9_ccppo_noledger.pt", {}),
}
COLS = (("success_all", "Success %", 100), ("urllc_success_all", "URLLC on-time %", 100),
        ("rejected_all", "Rejected %", 100), ("late_all", "Late %", 100),
        ("lat_p95_exec", "Lp95 exec (s)", 1), ("cloud_share_exec", "Cloud %", 100),
        ("locality_exec", "LI %", 100))


def quarantine_stats(folder: Path) -> dict:
    """How often quarantine was the reason a URLLC task had fewer options."""
    import csv
    n_urllc = n_quar = n_quar_reject = 0
    for f in glob.glob(str(folder / "tasks_seed*.csv")):
        for r in csv.DictReader(open(f)):
            if r["service_class"] != "URLLC":
                continue
            n_urllc += 1
            q = int(r["rej_reputation"] or 0) > 0
            n_quar += q
            n_quar_reject += q and r["outcome"] == "rejected_no_feasible"
    return {"urllc_tasks": n_urllc, "urllc_with_quarantined_server": n_quar,
            "urllc_rejected_while_some_server_quarantined": n_quar_reject}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regime", default="stress")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    out = REPO_ROOT / "results" / "ledger_ablation" / (a.regime + ("_smoke" if a.smoke else ""))
    sums, qs = [], {}
    for name, (model, ov) in VARIANTS.items():
        cfg = load_config(overrides={"workload.regime": a.regime, "consensus.mode": "off", **ov})
        seeds = cfg["seeds"]["eval"][:2] if a.smoke else cfg["seeds"]["eval"]
        pol = CCPPO.load(REPO_ROOT / "models" / model, cfg, name=name)
        sums.append(evaluate(pol, cfg, name, out, seeds, 400 if a.smoke else None))
        qs[name] = quarantine_stats(out / name)
    md = (f"Regime **{a.regime}**, seeds {sums[0]['seeds']}. p-values vs L1_full.\n\n"
          + table(sums, cols=COLS, ref="L1_full") + "\n\nQuarantine counts (pooled over seeds):\n\n"
          + "\n".join(f"- {k}: {v}" for k, v in qs.items()))
    (out / "table.md").write_text(md + "\n")
    print(md)


if __name__ == "__main__":
    main()
