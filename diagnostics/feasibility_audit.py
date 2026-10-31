"""Per-task feasibility diagnostics for the *current, unmodified* simulator.

This module does not change environment behaviour. It wraps an existing
``PPOEdgeEnv`` rollout and, before every action, records why each of the
20 servers is or is not feasible for the current task.

Outputs (CSV, one row per offered task):
    task fields, number of feasible servers, per-constraint rejection counts,
    number of servers failing more than one constraint, a primary rejection
    reason, a static-feasibility flag (would the task be feasible on an
    *idle* server?), and the chosen action / outcome.

A second CSV holds one row per (task, server) pair with every constraint
result, so multi-constraint failures are never collapsed into one label.

Primary-reason precedence (documented assumption, only used for the summary
label): routing > slice > memory > energy > deadline. All failed constraints
are always recorded separately.

Usage (from the repository root):
    python -m diagnostics.feasibility_audit --policy m8 --seed 100
    python -m diagnostics.feasibility_audit --policy random --seed 100
    python -m diagnostics.feasibility_audit --policy m7 --seed 100
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np

from env.ppo_env import PPOEdgeEnv
from env.server import Server

REPO_ROOT = Path(__file__).resolve().parent.parent
CONSTRAINTS = ("routing", "slice", "memory", "energy", "deadline")
PRECEDENCE = CONSTRAINTS  # order used to pick the primary reason


def server_constraint_row(env, task, server) -> dict:
    """Evaluate every constraint for one (task, server) pair, plus raw values."""
    reasons = env.feasibility_reasons(task, server)
    comps = env.latency_components(task, server)
    return {
        "server_id": server.id,
        "server_cluster": server.cluster,
        **{f"ok_{c}": bool(reasons[c]) for c in CONSTRAINTS},
        "feasible": bool(reasons["feasible"]),
        "n_failed": sum(not reasons[c] for c in CONSTRAINTS),
        "available_memory": server.available_memory,
        "available_energy": server.available_energy,
        "active_jobs": len(server.active_jobs),
        "active_same_slice": server.active_slice_count(task.service_class),
        "slice_capacity": server.slice_capacity.get(task.service_class, 0),
        **{f"L_{k}": v for k, v in comps.items()},
        "L_total": sum(comps.values()),
        "deadline_budget": task.deadline - task.arrival_time,
    }


def static_feasible(env, task) -> bool:
    """Would the task meet its deadline on some routable server if that
    server were completely idle (no queue)? Separates workload-impossible
    tasks from congestion-induced infeasibility."""
    for s in env.servers:
        if env.routing_region(task, s) >= 2:
            continue
        lat = (env.transmission_latency(task, s) + env.movement_latency(task, s)
               + env.processing_latency(task, s))
        if task.arrival_time + lat <= task.deadline and task.memory <= s.memory_capacity:
            return True
    return False


def primary_reason(rows: list[dict]) -> str:
    """Label for a zero-feasible task: the earliest constraint in PRECEDENCE
    such that every routable server fails it is not well defined when
    servers fail different constraints, so we use: for each server take its
    first failed constraint in precedence order; among *routable* servers,
    report the most frequent one."""
    routable = [r for r in rows if r["ok_routing"]]
    firsts = []
    for r in routable:
        for c in PRECEDENCE:
            if not r[f"ok_{c}"]:
                firsts.append(c)
                break
    if not firsts:
        return "none"
    return Counter(firsts).most_common(1)[0][0]


def make_policy(name: str, env: PPOEdgeEnv, seed: int):
    if name == "random":
        rng = np.random.default_rng(seed)

        def act(obs, mask):
            idx = np.flatnonzero(mask)
            # Same convention as the env: with no feasible action an arbitrary
            # (infeasible) server is submitted and the task fails.
            return int(rng.choice(idx)) if len(idx) else 0
        return act
    if name == "m8":
        from sb3_contrib import MaskablePPO
        model = MaskablePPO.load(str(REPO_ROOT / "models/m8_masked_ppo"), env=env)

        def act(obs, mask):
            a, _ = model.predict(obs, action_masks=mask, deterministic=True)
            return int(a)
        return act
    if name == "m7":
        from stable_baselines3 import PPO
        model = PPO.load(str(REPO_ROOT / "models/m7_ppo"), env=env)

        def act(obs, mask):
            a, _ = model.predict(obs, deterministic=True)
            return int(a)
        return act
    raise ValueError(f"unknown policy {name}")


def run(policy: str, seed: int, num_tasks: int, out_dir: Path) -> dict:
    env = PPOEdgeEnv(num_tasks=num_tasks, seed=seed)
    act = make_policy(policy, env, seed)
    obs, _ = env.reset()

    task_rows, pair_rows = [], []
    while True:
        core = env.env
        task = core.current_task
        rows = [server_constraint_row(core, task, s) for s in core.servers]
        mask = env.action_masks()
        # Invariant: mask must agree with the per-server diagnostic.
        assert [r["feasible"] for r in rows] == list(mask), "mask/diagnostic mismatch"

        action = act(obs, mask)
        mask_ok_for_action = bool(mask[action])
        obs, reward, terminated, truncated, info = env.step(action)

        n_feas = int(mask.sum())
        routable = [r for r in rows if r["ok_routing"]]
        trow = {
            "task_id": task.id, "service_class": task.service_class,
            "arrival_time": task.arrival_time, "deadline": task.deadline,
            "slack": task.deadline - task.arrival_time, "cluster": task.cluster,
            "cpu_cycles": task.cpu_cycles, "memory": task.memory, "payload": task.payload,
            "n_feasible": n_feas,
            "n_routable": len(routable),
            **{f"rej_{c}": sum(not r[f"ok_{c}"] for r in rows) for c in CONSTRAINTS},
            # rejections counted only among routable servers (more informative)
            **{f"rej_{c}_routable": sum(not r[f"ok_{c}"] for r in routable)
               for c in CONSTRAINTS if c != "routing"},
            "n_multi_fail_routable": sum(r["n_failed"] >= 2 for r in routable),
            "primary_reason": primary_reason(rows) if n_feas == 0 else "",
            "static_feasible": static_feasible(core, task),
            "min_L_total_routable": min(r["L_total"] for r in routable),
            "min_L_queue_routable": min(r["L_queue"] for r in routable),
            "action": action, "action_was_masked_feasible": mask_ok_for_action,
            "success": bool(info["success"]), "reward": float(reward),
            "latency": info["latency"],
        }
        task_rows.append(trow)
        for r in rows:
            pair_rows.append({"task_id": task.id, **r})
        if terminated or truncated:
            break

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{policy}_seed{seed}_n{num_tasks}"
    _write_csv(out_dir / f"{stem}_tasks.csv", task_rows)
    _write_csv(out_dir / f"{stem}_pairs.csv", pair_rows)

    zero = [t for t in task_rows if t["n_feasible"] == 0]
    summary = {
        "policy": policy, "seed": seed, "num_tasks": num_tasks,
        "outcomes_recorded": len(task_rows),
        "success": sum(t["success"] for t in task_rows),
        "zero_feasible": len(zero),
        "success_given_feasible": (
            sum(t["success"] for t in task_rows if t["n_feasible"] > 0)
            / max(1, sum(t["n_feasible"] > 0 for t in task_rows))),
        "masked_feasible_but_failed": sum(
            t["action_was_masked_feasible"] and not t["success"] for t in task_rows),
        "zero_feasible_by_class": dict(Counter(t["service_class"] for t in zero)),
        "zero_feasible_static_infeasible": sum(not t["static_feasible"] for t in zero),
        "zero_feasible_dynamic_only": sum(t["static_feasible"] for t in zero),
        "zero_feasible_primary_reason": dict(Counter(t["primary_reason"] for t in zero)),
        "static_infeasible_all_tasks": sum(not t["static_feasible"] for t in task_rows),
        "static_infeasible_by_class": dict(Counter(
            t["service_class"] for t in task_rows if not t["static_feasible"])),
        "class_counts": dict(Counter(t["service_class"] for t in task_rows)),
        "mean_feasible_actions": float(np.mean([t["n_feasible"] for t in task_rows])),
        # Among zero-feasible tasks, how many routable servers fail each check
        "zero_feasible_mean_rejections_routable": {
            c: float(np.mean([t[f"rej_{c}_routable"] for t in zero])) if zero else 0.0
            for c in CONSTRAINTS if c != "routing"},
        "zero_feasible_mean_multi_fail_routable": (
            float(np.mean([t["n_multi_fail_routable"] for t in zero])) if zero else 0.0),
    }
    (out_dir / f"{stem}_summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--policy", choices=["random", "m7", "m8"], default="m8")
    p.add_argument("--seed", type=int, default=100)
    p.add_argument("--num-tasks", type=int, default=1000)
    p.add_argument("--out", type=Path, default=REPO_ROOT / "results/audit")
    a = p.parse_args()
    print(json.dumps(run(a.policy, a.seed, a.num_tasks, a.out), indent=2))


if __name__ == "__main__":
    main()
