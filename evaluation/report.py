"""Turn evaluation summaries into Markdown tables with paired tests."""

from __future__ import annotations

import numpy as np

from .stats import mcnemar_p, paired_permutation_p

DEFAULT_COLS = (("success_all", "Success (all) %", 100), ("late_all", "Late %", 100),
                ("rejected_all", "Rejected %", 100), ("lat_p50_exec", "Lp50 exec (s)", 1),
                ("lat_p95_exec", "Lp95 exec (s)", 1), ("cloud_share_exec", "Cloud %", 100),
                ("locality_exec", "LI %", 100), ("energy_total_j", "Energy (J)", 1),
                ("throughput_ontime_per_s", "Thr (on-time/s)", 1))


def table(summaries: list[dict], cols=DEFAULT_COLS, ref: str | None = None) -> str:
    head = "| Config | " + " | ".join(c[1] for c in cols) + (" | p(seed perm) | p(McNemar, pooled) |" if ref else " |")
    sep = "|" + "---|" * (len(cols) + 1 + (2 if ref else 0))
    lines = [head, sep]
    base = next((s for s in summaries if s["name"] == ref), None)
    for s in summaries:
        cells = []
        for key, _, scale in cols:
            a = s["aggregate"].get(key)
            if a is None or not np.isfinite(a["mean"]):
                cells.append("n/a")      # metric not defined for this configuration
                continue
            cells.append(f"{a['mean'] * scale:.2f} ± {a['std'] * scale:.2f}")
        line = f"| {s['name']} | " + " | ".join(cells) + " |"
        if base is not None:
            if s is base:
                line += " ref | ref |"
            else:
                seeds = s["seeds"]
                pa = [s["per_seed"][k]["success_all"] for k in seeds]
                pb = [base["per_seed"][k]["success_all"] for k in seeds]
                sa = np.concatenate([s["_per_task_success"][k] for k in seeds])
                sb = np.concatenate([base["_per_task_success"][k] for k in seeds])
                line += f" {paired_permutation_p(pa, pb):.3f} | {mcnemar_p(sa, sb):.2g} |"
        lines.append(line)
    return "\n".join(lines)
