"""Rollout-level invariants (random feasible policy) and workload tests."""

import numpy as np
import pytest

from env.config import load_config
from env.ppo_env import PPOEdgeEnv
from env.task_generator import TaskGenerator


def _rollout(regime="stress", seed=7, n=400):
    env = PPOEdgeEnv(load_config(overrides={"workload.regime": regime}), num_tasks=n, seed=seed)
    _, info = env.reset(options={"workload_seed": seed})
    results = list(info["skipped"])
    rng = np.random.default_rng(seed)
    done = env.idx >= len(env.tasks)
    while not done:
        mask = env.action_masks()
        assert mask.any(), "wrapper must never ask for an action on an all-false mask"
        a = int(rng.choice(np.flatnonzero(mask)))
        _, _, done, _, info = env.step(a)
        assert info["result"]["outcome"] in ("on_time", "late")   # masked => executed
        results.append(info["result"])
        results += info["skipped"]
        for s in env.core.servers:
            assert s.available_memory >= 0 and s.available_energy >= 0
            assert all(j["finish_time"] > env.core.time for j in s.active_jobs)
    return env, results


def test_every_offered_task_gets_exactly_one_outcome():
    env, res = _rollout()
    assert len(res) == len(env.tasks) == 400
    assert sorted(r["task_id"] for r in res) == list(range(400))


def test_urllc_admitted_tasks_meet_predicted_deadline_without_noise():
    env = PPOEdgeEnv(load_config(overrides={"simulator.service_noise_cv": 0.0,
                                            "servers.degraded_servers": []}), num_tasks=300)
    env.reset(options={"workload_seed": 3})
    done = False
    while not done:
        a = int(np.flatnonzero(env.action_masks())[0])
        _, _, done, _, info = env.step(a)
        if info["result"]["service_class"] == "URLLC":
            assert info["result"]["outcome"] == "on_time"


def test_new_workload_each_training_episode():            # audit D9
    env = PPOEdgeEnv(load_config(), num_tasks=20, seed=10000)
    env.reset()
    first = [t.arrival_time for t in env.tasks]
    env.reset()
    assert [t.arrival_time for t in env.tasks] != first


def test_fixed_workload_seed_replays_identically():
    env = PPOEdgeEnv(load_config(), num_tasks=50)
    env.reset(options={"workload_seed": 38})
    a = [t.__dict__ for t in env.tasks]
    env.reset(options={"workload_seed": 38})
    assert a == [t.__dict__ for t in env.tasks]


def test_paper_deadline_bands_and_shares():               # audit D7
    cfg = load_config()["workload"]
    ts = TaskGenerator(cfg, seed=1).generate_episode(20000)
    bands = cfg["deadline_bands_s"]
    for t in ts:
        lo, hi = bands[t.service_class]
        assert lo <= t.deadline_slack <= hi
    share = sum(t.service_class == "eMBB" for t in ts) / len(ts)
    assert share == pytest.approx(0.5, abs=0.02)
    assert all(a.arrival_time < b.arrival_time for a, b in zip(ts, ts[1:]))
