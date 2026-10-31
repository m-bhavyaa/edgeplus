"""Per-sensor battery extension."""

import numpy as np
import pytest

from agents.baselines import GreedyMinLatency, LyapunovGreedy
from env.config import load_config
from env.factory import make_core
from env.sensors import SensorField
from evaluation.runner import run_episode
from tests.conftest import CLOUD, FAST_LOCAL_4, SLOW_LOCAL_4, make_task


@pytest.fixture
def scfg():
    return load_config(overrides={"sensors.enabled": True, "ledger.enabled": False,
                                  "simulator.service_noise_cv": 0.0})


def test_disabled_by_default_and_feature_sizes():
    core = make_core(load_config())
    assert core.sensors is None and core.state_dim == 7 + 9 * 31
    core2 = make_core(load_config(overrides={"sensors.enabled": True}))
    assert core2.state_dim == 9 + 10 * 31


def test_harvest_follows_day_cycle_and_caps_at_capacity(scfg):
    f = SensorField(scfg["sensors"], 10)
    b0 = f.b.copy()
    f.advance(100.0)                                  # first half of the day: sun
    assert np.all(f.b >= b0) and np.all(f.b <= f.B)
    assert f.harvest_power(150.0) == 0.0              # second half: night
    full = SensorField(scfg["sensors"], 10)
    full.b[:] = full.B
    full.advance(50.0)
    assert np.all(full.b == full.B)


def test_upload_energy_uses_airtime_not_backhaul(scfg):
    core = make_core(scfg)
    t = make_task(payload=5e6)
    e_cloud = core.sensor_upload_energy(t, core.servers[CLOUD])
    assert e_cloud == pytest.approx(0.1 * 5e6 / 50e6)  # 0.5 s backhaul not paid by sensor
    assert core.sensor_upload_energy(t, core.servers[SLOW_LOCAL_4]) > \
        core.sensor_upload_energy(t, core.servers[FAST_LOCAL_4])


def test_sensing_and_upload_drain_battery_and_queue(scfg):
    core = make_core(scfg)
    t = make_task(deadline=100)
    j = core.sensor_of(t)
    b0 = core.sensors.b[j]
    core.set_task(t)
    r = core.execute(FAST_LOCAL_4)
    e = 0.01 + core.sensor_upload_energy(t, core.servers[FAST_LOCAL_4])
    assert r["sensor_energy"] == pytest.approx(e)
    assert core.sensors.b[j] == pytest.approx(b0 - e)
    assert core.sensors.Z[j] == pytest.approx(max(0.0, e - 0.04))


def test_battery_mask_and_dropped_outcome(scfg):
    core = make_core(scfg)
    t = make_task(payload=2e7, deadline=100)
    j = core.sensor_of(t)
    core.sensors.b[j] = 0.01 + 0.045               # enough for sensing + cloud (0.04 J) only
    core.set_task(t)
    assert core.battery_feasible(t, core.servers[CLOUD])
    assert not core.battery_feasible(t, core.servers[SLOW_LOCAL_4])
    t2 = make_task(id=2, arrival_time=0.0)
    core.sensors.b[j] = 0.0                         # dead sensor
    core.set_task(t2)
    assert not core.get_action_mask().any()
    r = core.reject()
    assert r["outcome"] == "dropped_battery" and core.sensors.dropped == 1


def test_lyapunov_price_prefers_cheap_links(scfg):
    core = make_core(scfg)
    t = make_task(payload=1.2e7, service_class="eMBB", deadline=200)
    core.sensors.Z[core.sensor_of(t)] = 5.0
    core.set_task(t)
    mask = core.get_action_mask()
    ids = np.flatnonzero(mask)
    cheapest = min(ids, key=lambda i: core.sensor_upload_energy(t, core.servers[i]))
    assert LyapunovGreedy(V=1000.0).act(core, mask) == cheapest      # energy dominates
    fastest = min(ids, key=lambda i: core.total_latency(t, core.servers[i]))
    assert GreedyMinLatency().act(core, mask) == fastest             # V = 0 behaviour
    core.sensors.Z[:] = 0.0
    assert LyapunovGreedy(V=1000.0).act(core, mask) == fastest       # no debt -> no price


def test_episode_outcomes_complete_and_deterministic(scfg):
    scfg["workload"]["regime"] = "stress"
    a, _, st = run_episode(LyapunovGreedy(), scfg, 38, 800)
    b, _, _ = run_episode(LyapunovGreedy(), scfg, 38, 800)
    assert len(a) == 800 and [r["outcome"] for r in a] == [r["outcome"] for r in b]
    assert 0.0 <= st["sensors"]["sensor_battery_mean_frac"] <= 1.0
