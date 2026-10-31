"""M3-M5: one test per feasibility rule of the CURRENT simulator, plus edge cases.

These tests characterise existing behaviour; they are not claims that the
behaviour matches the paper (see reports/phase_a_audit.md).
"""

import pytest

from tests.conftest import make_task


def _server(env, sid):
    return env.servers[sid]


# ---------------- routing ----------------

def test_routing_allows_local_and_neighbor_clusters_only(env):
    task = make_task(cluster=0)  # neighbors of 0 are 1 and 3
    env.set_task(task)
    allowed = {s.cluster for s in env.servers if env.routing_feasible(task, s)}
    assert allowed == {0, 1, 3}


def test_non_neighbor_server_is_masked_out(env):
    task = make_task(cluster=0, deadline=1e6)
    env.set_task(task)
    mask = env.get_action_mask()
    for s in env.servers:
        if s.cluster not in (0, 1, 3):
            assert mask[s.id] == 0


# ---------------- deadline ----------------

def test_deadline_boundary_is_inclusive(env):
    task = make_task(cluster=4, deadline=100.0)
    env.set_task(task)
    s = _server(env, 9)  # fast local server, cluster 4
    lat = env.total_latency(task, s)
    task.deadline = task.arrival_time + lat
    assert env.deadline_feasible(task, s)
    task.deadline = task.arrival_time + lat - 1e-9
    assert not env.deadline_feasible(task, s)


def test_latency_components_for_idle_local_fast_server(env):
    task = make_task(cluster=4, cpu_cycles=2e9, payload=1e6)
    env.set_task(task)
    c = env.latency_components(task, _server(env, 9))
    assert c["processing"] == pytest.approx(1.0)          # 2e9 / 2e9
    assert c["transmission"] == pytest.approx(1e6 / 24e6)  # bandwidth * gain
    assert c["movement"] == 0.0
    assert c["queue"] == 0.0


def test_queue_latency_reflects_backlog(env):
    t1 = make_task(id=1, cluster=4, cpu_cycles=4e9, deadline=100)
    env.set_task(t1)
    assert env.execute(9)["success"]
    t2 = make_task(id=2, arrival_time=0.5, cluster=4, deadline=100)
    env.set_task(t2)
    # job 1 finishes at 0 + 0 + 2.0 = 2.0 s; now = 0.5 s
    assert env.queue_latency(_server(env, 9)) == pytest.approx(1.5)


# ---------------- memory ----------------

def test_memory_rule(env):
    task = make_task(cluster=4, memory=8192, deadline=1e6)
    env.set_task(task)
    assert env.memory_feasible(task, _server(env, 9))       # 8192 capacity
    assert not env.memory_feasible(task, _server(env, 8))   # 4096 capacity


def test_memory_released_after_finish(env):
    t1 = make_task(id=1, cluster=4, memory=8000, deadline=100)
    env.set_task(t1)
    r = env.execute(9)
    assert r["success"]
    assert _server(env, 9).available_memory == pytest.approx(192)
    env.set_task(make_task(id=2, arrival_time=r["finish_time"] + 1e-6, cluster=4))
    assert _server(env, 9).available_memory == 8192
    assert _server(env, 9).active_jobs == []


# ---------------- energy ----------------

def test_energy_rule_and_consumption(env):
    s = _server(env, 9)
    task = make_task(cluster=4, cpu_cycles=2e9, deadline=100)
    env.set_task(task)
    s.energy_used = s.energy_budget - 0.5  # needs 1.0 (processing seconds)
    assert not env.energy_feasible(task, s)
    s.energy_used = 0.0
    r = env.execute(9)
    assert r["energy"] == pytest.approx(1.0)
    assert s.energy_used == pytest.approx(1.0)


# ---------------- slice ----------------

def test_slice_capacity_rule(env):
    s = _server(env, 9)
    for i in range(10):
        s.add_job(task_id=100 + i, service_class="URLLC", memory=1,
                  start_time=0, finish_time=1e6)
    task = make_task(cluster=4, deadline=1e7)
    env.set_task(task)
    assert not env.slice_feasible(task, s)
    task.service_class = "eMBB"
    assert env.slice_feasible(task, s)


def test_unsupported_slice_rejected(env):
    s = _server(env, 9)
    s.supported_slices = ("eMBB",)
    task = make_task(cluster=4)
    env.set_task(task)
    assert not env.slice_feasible(task, s)


# ---------------- mask / execute ----------------

def test_mask_matches_feasibility_reasons(env):
    task = make_task(cluster=5, deadline=3.0)
    env.set_task(task)
    mask = env.get_action_mask()
    for s in env.servers:
        assert bool(mask[s.id]) == env.feasibility_reasons(task, s)["feasible"]


def test_infeasible_action_fails_and_changes_nothing(env):
    task = make_task(cluster=0, deadline=1e6)
    env.set_task(task)
    s = _server(env, 19)  # cluster 9, not routable from 0
    r = env.execute(19)
    assert r["success"] is False and r["reward"] == -10.0
    assert s.active_jobs == [] and s.energy_used == 0.0


def test_impossible_task_gives_all_zero_mask(env):
    # 1e12 cycles cannot finish in 1 s anywhere
    task = make_task(cluster=4, cpu_cycles=1e12, deadline=1.0)
    env.set_task(task)
    assert env.get_action_mask().sum() == 0


def test_time_cannot_move_backwards(env):
    env.set_task(make_task(arrival_time=5.0, deadline=20))
    with pytest.raises(ValueError):
        env.set_task(make_task(arrival_time=4.0, deadline=20))


def test_reset_clears_episode_state(env):
    env.set_task(make_task(cluster=4, deadline=100))
    env.execute(9)
    env.reset()
    assert env.time == 0.0 and env.current_task is None
    assert all(s.active_jobs == [] and s.energy_used == 0.0 for s in env.servers)
