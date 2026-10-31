"""Per-sensor energy preservation experiment (extension, NOT in the paper).

Same 5 evaluation seeds for every variant; ledger off (so the energy effect is not
mixed with ledger effects); battery model ON except in E0.

  E0_no_battery        greedy, sensors disabled (reference: unlimited sensor energy)
  E1_greedy            greedy min latency, battery mask on, energy-unaware
  E2_lyap_greedy_V1    drift-plus-penalty greedy, V = 1
  E3_lyap_greedy_V5    drift-plus-penalty greedy, V = 5
  E4_ccppo_l0          CCPPO trained with batteries, no energy price (lambda_E = 0)
  E5_ccppo_l1          CCPPO trained with the Lyapunov reward price (lambda_E = 1)
  E6_ccppo_l0_bias     E4 model + Lyapunov logit bias at inference (weight 1)

    python -m experiments.sensor_energy --regime stress
    python -m experiments.sensor_energy --regime stress --smoke
"""

from __future__ import annotations

import argparse

from agents.baselines import GreedyMinLatency, LyapunovGreedy
from agents.ccppo import CCPPO
from env.config import REPO_ROOT, load_config
from evaluation.report import table
from evaluation.runner import evaluate

COLS = (("success_all", "Success %", 100), ("dropped_battery_all", "Dropped (dead sensor) %", 100),
        ("sensor_ever_died_frac", "Sensors died %", 100),
        ("sensor_battery_mean_frac", "Mean battery left %", 100),
        ("sensor_battery_jain", "Battery fairness (Jain)", 1),
        ("sensor_energy_spent_j", "Sensor energy (J)", 1),
        ("lat_p95_exec", "Lp95 exec (s)", 1), ("cloud_share_exec", "Cloud %", 100))


def variants():
    yield "E0_no_battery", {"sensors.enabled": False}, lambda cfg: GreedyMinLatency()
    yield "E1_greedy", {}, lambda cfg: GreedyMinLatency()
    yield "E2_lyap_greedy_V1", {}, lambda cfg: LyapunovGreedy(1.0)
    yield "E3_lyap_greedy_V5", {}, lambda cfg: LyapunovGreedy(5.0)
    yield "E4_ccppo_l0", {}, lambda cfg: CCPPO.load(REPO_ROOT / "models/m9_ccppo_sens_l0.pt", cfg)
    yield "E5_ccppo_l1", {"sensors.lyapunov_weight": 1.0}, \
        lambda cfg: CCPPO.load(REPO_ROOT / "models/m9_ccppo_sens_l1.pt", cfg)

    def biased(cfg):
        p = CCPPO.load(REPO_ROOT / "models/m9_ccppo_sens_l0.pt", cfg)
        p.energy_bias = 1.0
        return p
    yield "E6_ccppo_l0_bias", {}, biased


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regime", default="stress")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    out = REPO_ROOT / "results" / "sensor_energy" / (a.regime + ("_smoke" if a.smoke else ""))
    sums = []
    for name, ov, make in variants():
        cfg = load_config(overrides={"workload.regime": a.regime, "ledger.enabled": False,
                                     "consensus.mode": "off", "sensors.enabled": True, **ov})
        seeds = cfg["seeds"]["eval"][:2] if a.smoke else cfg["seeds"]["eval"]
        pol = make(cfg)
        pol.name = name
        sums.append(evaluate(pol, cfg, name, out, seeds, 400 if a.smoke else None))
    cols = COLS
    md = (f"Regime **{a.regime}**, seeds {sums[0]['seeds']}. Mean ± std over seeds. "
          "p-values vs E1_greedy (success). E0 has no battery model (sensor columns n/a).\n\n"
          + table(sums, cols=cols, ref="E1_greedy"))
    (out / "table.md").write_text(md + "\n")
    print(md)


if __name__ == "__main__":
    main()
