"""Rollout-level invariants on the current simulator (random feasible policy)."""

import numpy as np

from env.ppo_env import PPOEdgeEnv
from env.task_generator import TaskGenerator


def _rollout(seed=7, n=300):
    env = PPOEdgeEnv(num_tasks=n, seed=seed)
    env.reset()
    rng = np.random.default_rng(seed)
    outcomes = []
    while True:
        task = env.env.current_task
        mask = env.action_masks()
        assert mask.dtype == bool and mask.shape == (20,)
        idx = np.flatnonzero(mask)
        a = int(rng.choice(idx)) if len(idx) else 0
        _, _, term, _, info = env.step(a)
        outcomes.append((task.id, bool(mask[a]), info["success"]))
        for s in env.servers:
            assert s.available_memory >= 0
            assert s.available_energy >= 0
            assert all(j["finish_time"] > env.env.time for j in s.active_jobs)
        if term:
            break
    return outcomes


def test_every_offered_task_gets_exactly_one_outcome():
    out = _rollout()
    assert len(out) == 300
    assert len({tid for tid, _, _ in out}) == 300


def test_masked_feasible_action_always_succeeds_and_vice_versa():
    # Execution re-runs the same checks on the same state, so success == mask[a].
    for _, feasible, success in _rollout():
        assert feasible == success


def test_generator_is_deterministic_under_seed():
    a = TaskGenerator(seed=3).generate_batch(50)
    b = TaskGenerator(seed=3).generate_batch(50)
    assert [t.__dict__ for t in a] == [t.__dict__ for t in b]


def test_generator_tasks_sorted_and_deadline_after_arrival():
    ts = TaskGenerator(seed=3).generate_batch(500)
    assert all(x.arrival_time <= y.arrival_time for x, y in zip(ts, ts[1:]))
    assert all(t.deadline > t.arrival_time for t in ts)
