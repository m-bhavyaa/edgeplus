"""M3-M5: one test per feasibility rule, timing model, and edge cases."""

import pytest

from env.edge_env import EdgePlusEnv
from tests.conftest import CLOUD, FAST_LOCAL_4, MOBILE_4, SLOW_LOCAL_4, make_task


def test_server_inventory(env):
    kinds = [s.kind for s in env.servers]
    assert len(env.servers) == 31
    assert kinds.count("mobile") == 10 and kinds.count("cloud") == 1


# ---------------- routing (paper order, Sec. III-C1) ----------------

def test_paper_routing_tiers(env):
    t = make_task(cluster=4)
    tiers = {s.id: env.routing_region(t, s) for s in env.servers}
    assert tiers[SLOW_LOCAL_4] == 0 and tiers[FAST_LOCAL_4] == 0
    assert tiers[MOBILE_4] == 1
    assert tiers[3 * 5 + 2] == 2          # mobile of neighbour cluster 5
    assert tiers[3 * 5 + 1] is None       # stationary of neighbour: not routable
    assert tiers[3 * 0 + 2] is None       # mobile of non-neighbour cluster 0
    assert tiers[CLOUD] == 3


def test_legacy_routing_allows_any_local_or_neighbor(cfg):
    cfg["simulator"]["routing"] = "legacy"
    e = EdgePlusEnv(cfg)
    t = make_task(cluster=0)
    allowed = {s.cluster for s in e.servers if e.routing_feasible(t, s)}
    assert allowed == {0, 1, 3}


# ---------------- latency / timing ----------------

def test_latency_components_idle_fast_local(env):
    t = make_task(cluster=4, cpu_cycles=2e9, payload=1e6)
    env.set_task(t)
    c = env.latency_components(t, env.servers[FAST_LOCAL_4])
    assert c["processing"] == pytest.approx(1.0)
    assert c["transmission"] == pytest.approx(1e6 / 24e6)
    assert c["movement"] == 0.0 and c["queue"] == 0.0 and c["consensus"] == 0.0


def test_movement_only_for_neighbor_mobiles(env):
    t = make_task(cluster=4)
    m5 = env.servers[3 * 5 + 2]
    assert env.movement_latency(t, m5) == pytest.approx(2000 / 33.3)
    assert env.movement_latency(t, env.servers[MOBILE_4]) == 0.0
    assert env.movement_latency(t, env.servers[CLOUD]) == 0.0


def test_cloud_adds_backhaul(env):
    t = make_task(payload=5e6)
    assert env.transmission_latency(t, env.servers[CLOUD]) == pytest.approx(5e6 / 50e6 + 0.5)


def test_finish_time_includes_transmission(env):          # audit D3
    t = make_task(cluster=4, payload=12e6, deadline=100)
    env.set_task(t)
    r = env.execute(FAST_LOCAL_4)
    assert r["start_time"] == pytest.approx(0.5)
    assert r["finish_time"] == pytest.approx(t.arrival_time + r["latency"])


def test_transmission_overlaps_queue(env):
    env.set_task(make_task(id=1, cluster=4, cpu_cycles=8e9, deadline=100))
    env.execute(FAST_LOCAL_4)                              # busy until ~4.04 s
    t2 = make_task(id=2, arrival_time=1.0, cluster=4, payload=24e6, deadline=100)
    env.set_task(t2)
    c = env.latency_components(t2, env.servers[FAST_LOCAL_4])
    # data ready at 2.0 s, server free at ~4.04 s -> queue ~2.04 s
    assert c["queue"] == pytest.approx(4.0 + 1e6 / 24e6 - 2.0)


def test_backlog_is_relative(env):                        # audit D2
    env.set_task(make_task(id=1, arrival_time=50.0, cluster=4, payload=1, deadline=100))
    env.execute(FAST_LOCAL_4)
    env.set_task(make_task(id=2, arrival_time=50.5, cluster=4, deadline=100))
    assert env.servers[FAST_LOCAL_4].backlog(env.time) == pytest.approx(0.5, abs=1e-6)


# ---------------- deadline ----------------

def test_deadline_boundary_inclusive(env):
    t = make_task(cluster=4, deadline=100.0)
    env.set_task(t)
    s = env.servers[FAST_LOCAL_4]
    t.deadline = env.total_latency(t, s)
    assert env.deadline_feasible(t, s)
    t.deadline -= 1e-9
    assert not env.deadline_feasible(t, s)


def test_deadline_mask_scope(cfg):
    t = make_task(cluster=4, service_class="eMBB", cpu_cycles=1e12, deadline=1.0)
    for scope, expected in (("all", False), ("urllc", True), ("none", True)):
        cfg["simulator"]["deadline_mask"] = scope
        e = EdgePlusEnv(cfg)
        e.set_task(t)
        assert e.deadline_feasible(t, e.servers[FAST_LOCAL_4]) is expected


# ---------------- memory / energy / slice ----------------

def test_memory_rule_and_release(env):
    t = make_task(cluster=4, memory=8000, deadline=100)
    env.set_task(t)
    assert not env.memory_feasible(t, env.servers[SLOW_LOCAL_4])
    r = env.execute(FAST_LOCAL_4)
    assert env.servers[FAST_LOCAL_4].available_memory == pytest.approx(192)
    env.set_task(make_task(id=2, arrival_time=r["finish_time"] + 1e-6))
    assert env.servers[FAST_LOCAL_4].available_memory == 8192


def test_energy_eq2_and_mobile_only_budget(env):
    t = make_task(cluster=4, cpu_cycles=2e9, payload=1e6)
    s = env.servers[MOBILE_4]
    e = 0.5 * (1e6 / 15e6) + 1e-9 * 2e9
    assert env.energy_required(t, s) == pytest.approx(e)
    s.energy_used = s.energy_budget - e / 2
    assert not env.energy_feasible(t, s)
    stat = env.servers[FAST_LOCAL_4]
    stat.energy_used = 1e12
    assert env.energy_feasible(t, stat)


def test_cluster_slice_budget(env):                        # audit D4
    # URLLC compute budget is 20 s per cluster; fill cluster 4 with 19.5 s.
    env.servers[SLOW_LOCAL_4].add_job(99, "URLLC", 1, 0.0, 19.5)
    t = make_task(cluster=4, cpu_cycles=2e9, deadline=1e6)
    env.set_task(t)
    assert not env.slice_feasible(t, env.servers[FAST_LOCAL_4])   # needs 1.0 s more
    assert env.slice_feasible(t, env.servers[CLOUD])              # cloud has no slice
    t.service_class = "eMBB"
    assert env.slice_feasible(t, env.servers[FAST_LOCAL_4])


# ---------------- mask / execute / outcomes ----------------

def test_mask_matches_reasons(env):
    t = make_task(cluster=5, deadline=3.0)
    env.set_task(t)
    m = env.get_action_mask()
    assert [bool(x) for x in m] == [env.is_feasible(t, s) for s in env.servers]


def test_infeasible_action_is_explicit_and_changes_nothing(env):
    env.set_task(make_task(cluster=0, deadline=1e6))
    r = env.execute(3 * 9)                                  # cluster 9 stationary
    assert r["outcome"] == "rejected_infeasible_action" and not r["success"]
    assert env.servers[27].active_jobs == []


def test_impossible_task_gives_all_false_mask_and_explicit_reject(env):
    env.set_task(make_task(cpu_cycles=1e13, deadline=1.0))
    assert not env.get_action_mask().any()
    r = env.reject()
    assert r["outcome"] == "rejected_no_feasible" and r["reward"] < 0


def test_late_outcome_possible_with_noise(cfg):
    cfg["simulator"]["service_noise_cv"] = 0.0
    cfg["servers"]["degraded_servers"] = [FAST_LOCAL_4]
    e = EdgePlusEnv(cfg)
    t = make_task(cluster=4, service_class="eMBB", cpu_cycles=2e9, deadline=1.5, payload=1)
    e.set_task(t)
    assert e.is_feasible(t, e.servers[FAST_LOCAL_4])       # eMBB: deadline not masked
    r = e.execute(FAST_LOCAL_4)
    assert r["outcome"] == "late" and r["processing"] == pytest.approx(1.8)


def test_time_cannot_move_backwards(env):
    env.set_task(make_task(arrival_time=5.0))
    with pytest.raises(ValueError):
        env.set_task(make_task(arrival_time=4.0))


def test_reset_clears_episode_state(env):
    env.set_task(make_task(deadline=100))
    env.execute(FAST_LOCAL_4)
    env.reset()
    assert env.time == 0.0 and env.current_task is None
    assert all(s.active_jobs == [] and s.energy_used == 0.0 for s in env.servers)


def test_observation_is_scaled(env):                       # audit D8
    env.set_task(make_task())
    obs = env.get_state()
    assert obs.shape == (env.state_dim,) and abs(obs).max() <= 5.0
