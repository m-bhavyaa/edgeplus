"""M12 ledger simulator and M14 consensus-delay model."""

import dataclasses

import numpy as np
import pytest

from env.config import load_config
from env.factory import make_core
from ledger import ConsensusDelayModel, Ledger, PartialBlock, block_hash
from tests.conftest import CLOUD, FAST_LOCAL_4, MOBILE_4, make_task


@pytest.fixture
def lcfg():
    return load_config()["ledger"]


def _log(i, server=13, cluster=4, on_time=True, t=1.0):
    return {"task": i, "cluster": cluster, "origin": cluster, "server": server,
            "class": "URLLC", "deadline": 10.0, "t_arrival": 0.0, "t_end": t,
            "on_time": on_time, "energy": 1.0}


def test_adaptive_block_size_eq21(lcfg):
    lg = Ledger(lcfg, 10)
    assert lg.block_size(4, rho=0.0) == lcfg["block_min"]
    assert lg.block_size(4, rho=1.0) == lcfg["block_max"]


def test_block_seals_at_size_and_chain_links(lcfg):
    lcfg["block_min"] = lcfg["block_max"] = 4             # fixed size for this test
    lg = Ledger(lcfg, 10)
    for i in range(12):
        lg.record(_log(i, t=1.0 + i * 1e-3))
    ch = lg.chains[4]
    assert len(ch.blocks) >= 2
    assert ch.blocks[1].prev_hash == ch.blocks[0].hash
    assert ch.blocks[0].hash == block_hash(ch.blocks[0].payload())


def test_block_seals_on_timeout(lcfg):
    lg = Ledger(lcfg, 10)
    lg.record(_log(0, t=1.0))
    lg.advance(1.0 + lcfg["block_timeout_s"] + 1e-9)
    assert len(lg.chains[4].blocks) == 1 and lg.chains[4].pending == []


def test_invalid_blocks_rejected(lcfg):
    lg = Ledger(lcfg, 10)
    bad_auth = PartialBlock(4, 0, [_log(0)], "genesis", "intruder", 1.0)
    bad_auth.hash = block_hash(bad_auth.payload())
    assert not lg.submit_block(bad_auth)
    good = PartialBlock(4, 0, [_log(0)], "genesis", "auth-4-0", 1.0)
    good.hash = block_hash(good.payload())
    tampered = dataclasses.replace(good, records=[_log(0, on_time=False)])
    assert not lg.submit_block(tampered)                   # hash no longer matches
    wrong_prev = dataclasses.replace(good, prev_hash="xyz")
    wrong_prev.hash = block_hash(wrong_prev.payload())
    assert not lg.submit_block(wrong_prev)
    assert lg.stats["rejected_blocks"] == 3
    assert lg.submit_block(good)


def test_reputation_ema_and_hinge(lcfg):
    lg = Ledger(lcfg, 10)
    assert lg.reputation(13) == 1.0 and lg.reputation_penalty(13) == 0.0
    for i in range(40):
        lg._update_feedback(_log(i, on_time=False))
    assert lg.reputation(13) == 0.0                         # EMA -> -kappa, clipped
    assert lg.reputation_penalty(13) == pytest.approx(lcfg["rep_threshold"])


def test_debt_is_relative_throughput_shortfall(lcfg):
    lg = Ledger(lcfg, 10)
    for c in range(10):
        for i in range(10 if c != 2 else 0):
            lg._update_feedback(_log(i, cluster=c))
    lg.now = 10.0
    assert lg.debt(2) == pytest.approx(1.0)
    assert lg.debt(0) == 0.0 and lg.debt(-1) == 0.0


def test_bft_rounds_commit_or_timeout(lcfg):
    lg = Ledger(lcfg, 10)
    lg.advance(3.5)
    assert lg.stats["bft_rounds"] == 3 and len(lg.global_blocks) == 3
    assert lg.verify_global(lg.global_blocks[0])
    lcfg["bft_faulty"] = 2                                  # n=4 tolerates f=1
    lg2 = Ledger(lcfg, 10)
    lg2.advance(3.5)
    assert lg2.stats["bft_timeouts"] == 3 and lg2.global_blocks == []


def test_ledger_deterministic_under_seed(lcfg):
    def run():
        lg = Ledger(lcfg, 10)
        lg.reset(5)
        for i in range(100):
            lg.record(_log(i, t=i * 0.01))
        return [b.hash for b in lg.chains[4].blocks], lg.stats["poa_delays"]
    assert run() == run()


def test_simulator_feeds_ledger_after_finish_and_quarantines():
    cfg = load_config(overrides={"simulator.service_noise_cv": 0.0})
    core = make_core(cfg)
    t = make_task(cluster=4, deadline=100)
    core.set_task(t)
    r = core.execute(FAST_LOCAL_4)
    assert core.ledger.stats["records"] == 0                # not logged before t_end
    core.set_task(make_task(id=2, arrival_time=r["finish_time"] + 1.0, deadline=200))
    assert core.ledger.stats["records"] == 1
    core.ledger.rep[FAST_LOCAL_4] = 0.1                     # low reputation
    assert not core.reputation_feasible(core.current_task, core.servers[FAST_LOCAL_4])
    embb = make_task(id=3, arrival_time=core.time, service_class="eMBB", deadline=500)
    assert core.reputation_feasible(embb, core.servers[FAST_LOCAL_4])


# ------------------------------------------------------------ consensus (M14)

def _model(path="edge", scale=1.0, dist="sampled", faulty=0):
    cfg = load_config()
    cfg["ledger"]["bft_faulty"] = faulty
    cc = {"mode": "mask_aware", "path": path, "delay_scale": scale,
          "distribution": dist, "max_retries": 3}
    return ConsensusDelayModel(cfg["ledger"], cc, Ledger(cfg["ledger"], 10)), cfg


def test_edge_path_delay_small_and_bounded():
    m, cfg = _model()
    core = make_core(cfg)
    t = make_task()
    ds = [m.sample_delay(t, core.servers[FAST_LOCAL_4], 1.0 + i * 0.01)[0] for i in range(200)]
    assert max(ds) <= cfg["ledger"]["block_timeout_s"] + 0.01
    assert m.expected_delay(t, core.servers[FAST_LOCAL_4], 3.0) > 0


def test_cloud_path_adds_bft_wait_only_off_cluster():
    m, cfg = _model(path="edge_cloud", dist="fixed")
    core = make_core(cfg)
    t = make_task(cluster=4)
    local = m.expected_delay(t, core.servers[FAST_LOCAL_4], 0.25)
    cloud = m.expected_delay(t, core.servers[CLOUD], 0.25)
    mobile_local = m.expected_delay(t, core.servers[MOBILE_4], 0.25)
    assert cloud - local == pytest.approx(0.75 + 0.0069 * np.exp(0.045), rel=1e-3)
    assert mobile_local == pytest.approx(local)


def test_broken_bft_quorum_times_out():
    m, cfg = _model(path="edge_cloud", faulty=2)
    core = make_core(cfg)
    d, timed_out = m.sample_delay(make_task(), core.servers[CLOUD], 0.5)
    assert timed_out and d >= 3 * (cfg["ledger"]["bft_timeout_s"] + 1.0)


def test_delay_scale_multiplies():
    m1, cfg = _model(dist="fixed")
    m10, _ = _model(dist="fixed", scale=10.0)
    core = make_core(cfg)
    t, s = make_task(), core.servers[FAST_LOCAL_4]
    assert m10.expected_delay(t, s, 1.0) == pytest.approx(10 * m1.expected_delay(t, s, 1.0))


def test_mask_aware_mode_tightens_deadline():
    cfg = load_config(overrides={"consensus.mode": "mask_aware", "consensus.path": "edge_cloud",
                                 "consensus.distribution": "fixed",
                                 "simulator.service_noise_cv": 0.0})
    core = make_core(cfg)
    t = make_task(cluster=4, cpu_cycles=1e9, payload=1e6, deadline=1.4)
    core.set_task(t)
    # cloud: tx 0.52 + proc 0.1 = 0.62 s, but BFT wait ~1 s makes it infeasible
    assert not core.deadline_feasible(t, core.servers[CLOUD])
    cfg["consensus"]["mode"] = "report_only"
    assert core.deadline_feasible(t, core.servers[CLOUD])
