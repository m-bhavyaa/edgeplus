"""Unified evaluator: same workloads, same rejection rule, per-task export.

For each evaluation seed the workload is regenerated from that seed, so every
policy sees the identical task sequence (paired comparison). Policies are
frozen: nothing here calls a training routine.
"""

from __future__ import annotations

import csv
import json
import subprocess
import time
from pathlib import Path

from diagnostics.feasibility import diagnose_task
from env.config import REPO_ROOT
from env.factory import make_core
from env.task_generator import TaskGenerator

from .metrics import summarize
from .stats import mean_ci

ROW_KEYS = ("task_id", "service_class", "cluster", "arrival_time", "deadline", "outcome",
            "success", "executed", "server_id", "server_kind", "server_cluster", "routing_tier",
            "latency", "consensus", "consensus_timeout", "transmission", "movement", "queue",
            "processing", "energy", "start_time", "finish_time", "reward", "n_feasible",
            "n_routable", "rej_slice", "rej_memory", "rej_energy", "rej_reputation",
            "rej_deadline", "n_multi_fail", "primary_reason", "decision_ms")


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def run_episode(policy, cfg: dict, workload_seed: int, num_tasks: int | None = None):
    core = make_core(cfg, seed=workload_seed)
    tasks = TaskGenerator(cfg["workload"], workload_seed).generate_episode(num_tasks)
    if hasattr(policy, "reset"):
        policy.reset(core)
    rows = []
    for task in tasks:
        core.set_task(task)
        diag = diagnose_task(core, task)
        mask = core.get_action_mask()
        assert bool(mask.any()) == (diag["n_feasible"] > 0)
        if not mask.any():
            res, ms = core.reject(), None
        else:
            t0 = time.perf_counter()
            action = policy.act(core, mask)
            ms = (time.perf_counter() - t0) * 1e3
            res = core.execute(action)
        rows.append({k: {**res, **diag, "decision_ms": ms}.get(k) for k in ROW_KEYS})
    if len(rows) != len(tasks):
        raise RuntimeError(f"recorded {len(rows)} outcomes for {len(tasks)} offered tasks")
    util = [{"server_id": s.id, "kind": s.kind, "cluster": s.cluster,
             "tasks": sum(r["server_id"] == s.id and r["executed"] for r in rows),
             "busy_s": sum(r["processing"] for r in rows if r["server_id"] == s.id and r["executed"]),
             "energy_used": s.energy_used} for s in core.servers]
    ledger_stats = None
    if core.ledger is not None:
        st = core.ledger.stats
        ledger_stats = {k: v for k, v in st.items() if not isinstance(v, list)}
        for k in ("poa_delays", "bft_delays"):
            ledger_stats[k + "_median_ms"] = (1e3 * float(sorted(st[k])[len(st[k]) // 2])
                                              if st[k] else None)
    return rows, util, ledger_stats


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def evaluate(policy, cfg: dict, name: str, out_dir: Path, seeds=None,
             num_tasks: int | None = None, save_tasks: bool = True) -> dict:
    """Evaluate one policy on all seeds; write per-task CSVs and a summary JSON."""
    seeds = seeds or cfg["seeds"]["eval"]
    out_dir = Path(out_dir) / name
    out_dir.mkdir(parents=True, exist_ok=True)
    per_seed = {}
    per_task_success = {}
    for s in seeds:
        rows, util, lstats = run_episode(policy, cfg, s, num_tasks)
        per_seed[s] = summarize(rows, cfg["workload"]["horizon_s"])
        if lstats:
            per_seed[s]["ledger"] = lstats
        per_task_success[s] = [r["success"] for r in rows]
        if save_tasks:
            _write_csv(out_dir / f"tasks_seed{s}.csv", rows)
            _write_csv(out_dir / f"servers_seed{s}.csv", util)
    keys = [k for k, v in per_seed[seeds[0]].items() if isinstance(v, (int, float))]
    agg = {k: mean_ci([per_seed[s][k] for s in seeds]) for k in keys}
    summary = {"name": name, "seeds": list(seeds), "num_tasks": num_tasks,
               "regime": cfg["workload"]["regime"], "git_commit": git_commit(),
               "aggregate": agg, "per_seed": per_seed}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    (out_dir / "config.json").write_text(json.dumps(cfg, indent=2))
    summary["_per_task_success"] = per_task_success
    return summary
