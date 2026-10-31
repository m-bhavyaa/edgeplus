"""Known defects found in the Phase A audit (reports/phase_a_audit.md).

Each test asserts the CORRECT behaviour and is marked ``xfail(strict=True)``
against the current code. They are listed as XFAIL in the pytest summary, and
because ``xfail_strict = true`` a test that starts passing (i.e. after the
defect is fixed) turns into a failure until its marker is removed. This keeps
known defects visible without making the suite red before Phase B.
"""

import ast
from pathlib import Path

import pytest

from env.ppo_env import PPOEdgeEnv
from env.task_generator import TaskGenerator
from tests.conftest import make_task

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.xfail(reason="D1: evaluate-m7.py loads the M8 checkpoint", strict=True)
def test_D1_evaluate_m7_loads_m7_checkpoint():
    src = (ROOT / "evaluate-m7.py").read_text()
    assert "models/m7_ppo" in src


@pytest.mark.xfail(reason="D2: Server.queue_time is absolute last finish time, not backlog",
                   strict=True)
def test_D2_observed_queue_is_relative_backlog(env):
    env.set_task(make_task(id=1, arrival_time=50.0, cluster=4, deadline=100))
    env.execute(9)                       # 2e9 cycles / 2e9 Hz -> finishes at 51.0 s
    env.set_task(make_task(id=2, arrival_time=50.5, cluster=4, deadline=100))
    # Remaining backlog at t=50.5 is 0.5 s; current code reports 51.0.
    queue_feature = env.get_state()[5 + 9 * 6 + 4]
    assert queue_feature == pytest.approx(0.5)


@pytest.mark.xfail(reason="D3: server finish_time ignores transmission/movement delay",
                   strict=True)
def test_D3_server_finish_time_matches_reported_completion(env):
    task = make_task(cluster=4, payload=12e6, deadline=100)   # 0.5 s tx on server 9
    env.set_task(task)
    r = env.execute(9)
    assert r["finish_time"] == pytest.approx(task.arrival_time + r["latency"])


@pytest.mark.xfail(reason="D4: no cluster-level slice budget (paper Eq. 4)", strict=True)
def test_D4_cluster_slice_quota_is_enforced(env):
    # Fill cluster 4's URLLC quota (10) using 5 jobs on each of its two servers.
    for sid in (8, 9):
        for i in range(5):
            env.servers[sid].add_job(task_id=1000 + 10 * sid + i, service_class="URLLC",
                                     memory=1, start_time=0, finish_time=1e6)
    task = make_task(cluster=4, deadline=1e7)
    env.set_task(task)
    assert not env.slice_feasible(task, env.servers[9])


@pytest.mark.xfail(reason="D7: deadline bands differ from paper Sec. IV-B2", strict=True)
def test_D7_deadline_bands_match_paper():
    bands = {"URLLC": (5, 15), "eMBB": (30, 120), "mMTC": (120, 600)}
    for t in TaskGenerator(seed=1).generate_batch(3000):
        lo, hi = bands[t.service_class]
        assert lo <= t.deadline_slack <= hi


@pytest.mark.xfail(reason="D7: class shares 1/3 each instead of 20/50/30 (Table IV)",
                   strict=True)
def test_D7_class_shares_match_paper():
    ts = TaskGenerator(seed=1).generate_batch(20000)
    share = sum(t.service_class == "eMBB" for t in ts) / len(ts)
    assert abs(share - 0.50) < 0.02


@pytest.mark.xfail(reason="D9: every training episode replays the same workload", strict=True)
def test_D9_training_episodes_use_different_workloads():
    env = PPOEdgeEnv(num_tasks=20, seed=42)
    env.reset()
    first = [t.arrival_time for t in env.tasks]
    env.reset()
    assert [t.arrival_time for t in env.tasks] != first


@pytest.mark.xfail(reason="D8: observation not scaled (raw CPU cycles ~1e9)", strict=True)
def test_D8_observation_is_scaled():
    env = PPOEdgeEnv(num_tasks=10, seed=1)
    obs, _ = env.reset()
    assert abs(obs).max() < 100


@pytest.mark.xfail(reason="D15: edge_env.py keeps two superseded classes in a string literal",
                   strict=True)
def test_D15_no_dead_code_string_blocks():
    tree = ast.parse((ROOT / "env/edge_env.py").read_text())
    big_strings = [n for n in tree.body if isinstance(n, ast.Expr)
                   and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)
                   and len(n.value.value) > 2000]
    assert not big_strings
