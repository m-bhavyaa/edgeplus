"""Build a simulator with the optional ledger (M12) and consensus model (M14) wired in."""

from __future__ import annotations

from .edge_env import EdgePlusEnv


def make_components(cfg: dict):
    ledger = consensus = None
    if cfg["ledger"]["enabled"]:
        from ledger import Ledger
        ledger = Ledger(cfg["ledger"], cfg["workload"]["num_clusters"])
    if cfg["consensus"]["mode"] != "off":
        from ledger import ConsensusDelayModel
        consensus = ConsensusDelayModel(cfg["ledger"], cfg["consensus"], ledger)
    return ledger, consensus


def make_core(cfg: dict, seed: int = 0) -> EdgePlusEnv:
    ledger, consensus = make_components(cfg)
    return EdgePlusEnv(cfg, seed=seed, ledger=ledger, consensus=consensus)
