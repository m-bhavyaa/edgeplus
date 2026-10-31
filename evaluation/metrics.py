"""KPIs (paper Table V) computed from per-task rows.

Denominators are stated in every key name:
    *_all       over all OFFERED tasks
    *_exec      over EXECUTED tasks (on_time + late); rejected tasks have no latency
    *_feasible  over tasks with >= 1 feasible server
"""

from __future__ import annotations

import numpy as np


def summarize(rows: list[dict], horizon_s: float) -> dict:
    n = len(rows)
    out = {k: sum(r["outcome"] == k for r in rows) for k in
           ("on_time", "late", "rejected_no_feasible", "rejected_infeasible_action")}
    ex = [r for r in rows if r["executed"]]
    feas = [r for r in rows if r["n_feasible"] > 0]
    lat = np.array([r["latency"] for r in ex]) if ex else np.array([np.nan])
    urllc = [r for r in rows if r["service_class"] == "URLLC"]
    on_by_cluster = np.bincount([r["cluster"] for r in rows if r["success"]], minlength=10)
    jain = (on_by_cluster.sum() ** 2 / (len(on_by_cluster) * (on_by_cluster ** 2).sum())
            if on_by_cluster.any() else 0.0)
    # Span from t=0 to the last arrival or completion (horizon_s is only a lower bound
    # for full-length episodes; truncated smoke episodes end earlier).
    makespan = max([r["arrival_time"] for r in rows] + [r["finish_time"] for r in ex])
    if len(rows) and rows[-1]["arrival_time"] > 0.9 * horizon_s:
        makespan = max(makespan, horizon_s)

    def mean_ex(k):
        return float(np.mean([r[k] for r in ex])) if ex else float("nan")

    return {
        "tasks_offered": n,
        **{f"n_{k}": v for k, v in out.items()},
        "success_all": out["on_time"] / n,
        "violation_all": 1 - out["on_time"] / n,
        "late_all": out["late"] / n,
        "rejected_all": (out["rejected_no_feasible"] + out["rejected_infeasible_action"]) / n,
        "no_feasible_all": out["rejected_no_feasible"] / n,
        "feasibility_coverage_all": len(feas) / n,
        "success_feasible": (sum(r["success"] for r in feas) / len(feas)) if feas else float("nan"),
        "mean_feasible_servers_all": float(np.mean([r["n_feasible"] for r in rows])),
        "lat_mean_exec": float(np.nanmean(lat)),
        "lat_p50_exec": float(np.nanpercentile(lat, 50)),
        "lat_p95_exec": float(np.nanpercentile(lat, 95)),
        **{f"{k}_mean_exec": mean_ex(k) for k in
           ("queue", "processing", "transmission", "movement", "consensus")},
        "consensus_timeouts": sum(bool(r.get("consensus_timeout")) for r in ex),
        "energy_total_j": float(sum(r["energy"] for r in ex)),
        "throughput_ontime_per_s": out["on_time"] / makespan,
        "locality_exec": (sum(r["server_cluster"] == r["cluster"] for r in ex) / len(ex)) if ex else 0.0,
        "cloud_share_exec": (sum(r["server_kind"] == "cloud" for r in ex) / len(ex)) if ex else 0.0,
        "stationary_share_exec": (sum(r["server_kind"] == "stationary" for r in ex) / len(ex)) if ex else 0.0,
        "urllc_success_all": (sum(r["success"] for r in urllc) / len(urllc)) if urllc else float("nan"),
        "jain_fairness_clusters": float(jain),
        "reward_mean_all": float(np.mean([r["reward"] for r in rows])),
        "decision_ms_mean": float(np.mean([r["decision_ms"] for r in rows if r["decision_ms"] is not None]
                                          or [0.0])),
    }
