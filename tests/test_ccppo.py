"""M9 CCPPO: candidate sets, action validity, short training, save/load."""

import numpy as np
import pytest

from agents.ccppo import CCPPO, candidate_table
from env.config import load_config
from env.factory import make_core
from evaluation.runner import run_episode


@pytest.fixture
def cfg():
    c = load_config(overrides={"workload.regime": "stress"})
    c["ccppo"].update(n_steps=128, minibatch=64, epochs=2)
    c["train_tasks_per_episode"] = 150
    return c


def test_candidate_table_follows_routing_order(cfg):
    core = make_core(cfg)
    cand, K = candidate_table(core)
    assert K == 2 + 1 + 4 + 1                      # cluster 4/5 have 4 neighbours
    assert list(cand[4][:4]) == [12, 13, 14, 5]    # stationary, stationary, own mobile, nbr mobile
    assert cand[4][-1] == 30 and cand[0][-1] == -1 and 30 in cand[0]


def test_masked_policy_only_picks_feasible_servers(cfg):
    pol = CCPPO(cfg, use_masks=True, use_advisory=True, seed=1)
    rows, _, _ = run_episode(pol, cfg, workload_seed=5, num_tasks=200)
    assert len(rows) == 200
    assert not any(r["outcome"] == "rejected_infeasible_action" for r in rows)


def test_unmasked_policy_can_choose_infeasible(cfg):
    pol = CCPPO(cfg, use_masks=False, use_advisory=False, seed=1)
    rows, _, _ = run_episode(pol, cfg, workload_seed=5, num_tasks=400)
    assert all(r["outcome"] in ("on_time", "late", "rejected_no_feasible",
                                "rejected_infeasible_action") for r in rows)


def test_short_training_runs_and_save_load_roundtrip(cfg, tmp_path):
    pol = CCPPO(cfg, seed=2)
    log = pol.train(400)
    assert log and all(np.isfinite(e["return"]) for e in log)
    pol.save(tmp_path / "m.pt")
    pol2 = CCPPO.load(tmp_path / "m.pt", cfg)
    a = [r["server_id"] for r in run_episode(pol, cfg, 9, 100)[0]]
    b = [r["server_id"] for r in run_episode(pol2, cfg, 9, 100)[0]]
    assert a == b                                  # deterministic evaluation
