"""M14: consensus-delay-aware feasibility (extension beyond the paper).

Compares, on identical workloads and seeds:
    C0 no consensus delay (paper timing: ledger logging after execution)
    report_only   consensus delay is added to the real latency, mask ignores it  (mode C)
    mask_aware    consensus delay is added to latency AND to the deadline check   (mode B)
for path = edge (PoA only) and edge_cloud (PoA + BFT for off-cluster placements),
delay_scale in {1, 10, 50}, plus a broken-BFT-quorum scenario (faulty = 2 of 4).

    python run_consensus_extension.py --regime stress
    python run_consensus_extension.py --regime stress --smoke
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agents.baselines import GreedyMinLatency
from agents.ccppo import CCPPO
from env.config import REPO_ROOT, load_config
from evaluation.report import table
from evaluation.runner import evaluate

COLS = (("success_all", "Success (all) %", 100), ("urllc_success_all", "URLLC on-time %", 100),
        ("late_all", "Late %", 100), ("rejected_all", "Rejected %", 100),
        ("lat_p95_exec", "Lp95 exec (s)", 1), ("consensus_mean_exec", "Mean L_cons (s)", 1),
        ("consensus_timeouts", "Confirm. failures", 1), ("cloud_share_exec", "Cloud %", 100),
        ("energy_total_j", "Energy (J)", 1), ("throughput_ontime_per_s", "Thr (on-time/s)", 1))


def scenarios(smoke: bool):
    scales = [1.0, 50.0] if smoke else [1.0, 10.0, 50.0]
    yield "C0_no_consensus", {"consensus.mode": "off"}, None
    for path in ("edge", "edge_cloud"):
        for sc in scales:
            group = f"{path}_x{sc:g}"
            for mode in ("report_only", "mask_aware"):
                yield f"{group}_{mode}", {"consensus.mode": mode, "consensus.path": path,
                                          "consensus.delay_scale": sc}, group
    for mode in ("report_only", "mask_aware"):
        yield f"bft_faulty_{mode}", {"consensus.mode": mode, "consensus.path": "edge_cloud",
                                     "ledger.bft_faulty": 2}, "bft_faulty"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regime", default="stress")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "results" / "consensus")
    a = ap.parse_args()
    out = a.out / (a.regime + ("_smoke" if a.smoke else ""))
    md = [f"# M14 consensus extension: regime {a.regime}\n",
          "Each block compares report_only (mask ignores L_cons) with mask_aware on the same "
          "tasks; p-values are vs report_only. Mean ± std over seeds.\n"]
    index = {}
    for pol_name in ("ccppo", "greedy"):
        groups: dict = {}
        for name, ov, group in scenarios(a.smoke):
            cfg = load_config(overrides={"workload.regime": a.regime, **ov})
            seeds = cfg["seeds"]["eval"][:2] if a.smoke else cfg["seeds"]["eval"]
            n = 400 if a.smoke else None
            pol = (CCPPO.load(REPO_ROOT / "models" / "m9_ccppo.pt", cfg, name=name)
                   if pol_name == "ccppo" else GreedyMinLatency())
            pol.name = name
            s = evaluate(pol, cfg, name, out / pol_name, seeds, n)
            groups.setdefault(group, []).append(s)
            index[f"{pol_name}/{name}"] = {k: s["aggregate"][k]["mean"] for k, *_ in COLS}
        md.append(f"\n## Policy: {pol_name}\n")
        md.append(table(groups[None], cols=COLS))
        for g, sums in groups.items():
            if g is None:
                continue
            md.append(f"\n### {g}\n")
            md.append(table(sums, cols=COLS, ref=sums[0]["name"]))
    (out / "table.md").write_text("\n".join(md) + "\n")
    (out / "index.json").write_text(json.dumps(index, indent=2))
    print("\n".join(md))


if __name__ == "__main__":
    main()
