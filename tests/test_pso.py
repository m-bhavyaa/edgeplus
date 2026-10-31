"""M11 constricted PSO."""

import numpy as np
import pytest

from optimizer import ConstrictedPSO, constriction, sla_ok

SLA = {"max_cloud": 0.07, "max_fail": 0.05, "min_stationary": 0.80}


def _metrics(success, cloud=0.0, viol=None, stat=0.9):
    return {"success_all": success, "violation_all": 1 - success if viol is None else viol,
            "cloud_share_exec": cloud, "stationary_share_exec": stat, "lat_p95_exec": 1.0}


def test_constriction_coefficient():
    assert constriction(2.05, 2.05) == pytest.approx(0.7298, abs=1e-4)
    with pytest.raises(ValueError):
        constriction(2.0, 2.0)


def _params(**kw):
    p = {"particles": 8, "iterations": 15, "w_max": 0.9, "w_min": 0.4, "c1": 2.05, "c2": 2.05,
         "bounds": [[-5, 5], [-5, 5]], "sla": SLA}
    p.update(kw)
    return p


def test_pso_finds_optimum_of_smooth_function_and_stays_in_bounds():
    target = np.array([1.5, -2.0])
    f = lambda x: _metrics(float(np.exp(-np.sum((x - target) ** 2))), viol=0.0)  # noqa: E731
    out = ConstrictedPSO(_params(), seed=0).run(f, np.array([4.0, 4.0]))
    assert np.allclose(out["best"], target, atol=0.3)
    assert all(-5 <= v <= 5 for h in out["history"] for v in h["x"])
    assert out["accepted"]


def test_sla_gate_blocks_better_but_unsafe_basin():
    f = lambda x: _metrics(float(x[0] / 10), cloud=0.5 if x[0] > 0 else 0.0, viol=0.0)  # noqa: E731
    out = ConstrictedPSO(_params(bounds=[[-5, 5]]), seed=1).run(f, np.array([-1.0]))
    assert out["best_metrics"]["success_all"] > out["incumbent_metrics"]["success_all"]
    assert not out["accepted"] and out["adopted"] == [-1.0]


def test_sla_ok():
    assert sla_ok(_metrics(0.97, cloud=0.05, viol=0.03), SLA)
    assert not sla_ok(_metrics(0.97, cloud=0.05, viol=0.03, stat=0.5), SLA)


def test_pso_deterministic_under_seed():
    f = lambda x: _metrics(float(-np.sum(x ** 2)), viol=0.0)  # noqa: E731
    a = ConstrictedPSO(_params(), seed=3).run(f, np.zeros(2))["history"]
    b = ConstrictedPSO(_params(), seed=3).run(f, np.zeros(2))["history"]
    assert a == b
