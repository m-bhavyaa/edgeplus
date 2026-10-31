"""M10 advisory layer."""

import numpy as np
import pytest

from advisory import AdvisoryLayer, masked_probs
from advisory.nash import nash_shares
from advisory.pid import (PID, closed_loop_poly, fopdt_discrete, jury_stable, pid_discrete,
                          robustness_check, ziegler_nichols_fopdt)
from env.config import load_config
from env.factory import make_core
from env.topology import Topology
from tests.conftest import FAST_LOCAL_4, make_task


@pytest.fixture
def acfg():
    return load_config()["advisory"]


def test_nash_uncoupled_matches_closed_form(acfg):
    p = dict(acfg["nash"], coupling=0.0)
    rho = np.array([0.0, 0.4, 0.8] + [0.0] * 7)
    s, _ = nash_shares(rho, np.zeros(10), Topology().neighbors, p)
    # argmax of -a s rho - g (s-1)^2  ->  s = 1 - a rho / (2 g), on a 0.025 grid
    for c in range(3):
        assert s[c] == pytest.approx(1 - rho[c] / 2, abs=0.0125)


def test_nash_converges_and_respects_bounds(acfg):
    rng = np.random.default_rng(0)
    s, iters = nash_shares(rng.uniform(0, 1, 10), np.zeros(10), Topology().neighbors, acfg["nash"])
    assert iters < acfg["nash"]["max_iter"]
    assert np.all((s >= acfg["nash"]["s_min"]) & (s <= acfg["nash"]["s_max"]))


def test_pid_output_clipped_and_signed():
    pid = PID(1.9, 1.2, 0.06, 1.0)
    assert pid.step(0.3) > 0
    assert -1.0 <= pid.step(10.0) <= 1.0 and PID(1, 0, 0, 1).step(-5) == -1.0


def test_jury_matches_numpy_roots():
    rng = np.random.default_rng(1)
    for _ in range(200):
        c = np.concatenate([[1.0], rng.uniform(-1.5, 1.5, 3)])
        assert jury_stable(c) == bool(np.all(np.abs(np.roots(c)) < 1))


def test_zn_gains_and_closed_loop_poly():
    kp, ki, kd = ziegler_nichols_fopdt(1.0, 2.0, 0.5)
    assert (kp, ki, kd) == pytest.approx((4.8, 4.8, 1.2))
    poly = closed_loop_poly(fopdt_discrete(1, 2, 0.5, 0.1), pid_discrete(1.0, 0.5, 0.0, 0.1))
    assert poly[0] == 1.0


def test_robustness_check_has_nine_rows():
    rows = robustness_check(1.9, 1.2, 0.06, 1.0, 2.0, 0.5, 0.1)
    assert len(rows) == 9 and all(r["stable"] for r in rows)


def test_masked_softmax_never_selects_infeasible():
    logits = np.array([100.0, 0.0, -1.0])
    mask = np.array([False, True, True])
    p = masked_probs(logits, mask)
    assert p[0] == 0.0 and p.sum() == pytest.approx(1.0)
    with pytest.raises(ValueError):
        masked_probs(logits, np.zeros(3, bool))


def test_layer_bias_shape_and_effect(acfg):
    core = make_core(load_config(overrides={"ledger.enabled": False}))
    layer = AdvisoryLayer(acfg, 10)
    core.servers[FAST_LOCAL_4].add_job(1, "eMBB", 1, 0.0, 100.0)   # overload cluster 4
    core.set_task(make_task(arrival_time=1.0))
    b = layer.bias(core)
    assert b.shape == (31,) and b[30] == 0.0
    assert b[12] < b[0]          # cluster-4 server less attractive than idle cluster-0 server
