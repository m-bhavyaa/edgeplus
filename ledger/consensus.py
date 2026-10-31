"""Consensus-delay model for the M14 extension (NOT in the paper).

In the paper, edge PoA logs a task AFTER it finishes and cloud BFT is off the
critical path, so consensus never delays a task. The extension instead
assumes SYNCHRONOUS ADMISSION COMMIT: an assignment is dispatched only after
its assignment record is committed.

  path = "edge":       L_cons = batching wait + PoA validation
  path = "edge_cloud": additionally, placements outside the home cluster
                       (neighbour mobile or cloud) wait for the next BFT round
                       plus BFT delay; if the BFT quorum is broken (faulty > f)
                       each round times out and is retried up to max_retries.

Batching wait: a record waits until its block seals, i.e. until S_c records have
arrived or block_timeout_s passes, so wait ~ U(0, min(T_block, S_c / lam_c)).
lam_c is the recent assignment rate of the cluster (load dependent).

expected_delay() is what a consensus-aware MASK uses; sample_delay() is what
actually happens. distribution="fixed" makes both equal.
All delays are multiplied by delay_scale (used for sensitivity sweeps).
"""

from __future__ import annotations

import numpy as np

from env.server import CLOUD


class ConsensusDelayModel:

    def __init__(self, ledger_cfg: dict, cons_cfg: dict, ledger=None):
        self.lc = ledger_cfg
        self.cc = cons_cfg
        self.ledger = ledger
        self.reset(0)

    def reset(self, seed: int) -> None:
        self.rng = np.random.default_rng(seed + 7919)
        self._times: dict[int, list] = {}
        self.timeouts = 0

    # --------------------------------------------------------------- helpers
    def _rate(self, cluster: int, now: float, window: float = 10.0) -> float:
        ts = [t for t in self._times.get(cluster, []) if t > now - window]
        self._times[cluster] = ts
        return max(len(ts) / window, 1e-3)

    def _batch_cap(self, cluster: int, now: float) -> float:
        size = self.ledger.block_size(cluster) if self.ledger else self.lc["block_min"]
        return min(self.lc["block_timeout_s"], size / self._rate(cluster, now))

    def _needs_bft(self, task, server) -> bool:
        return self.cc["path"] == "edge_cloud" and (
            server.kind == CLOUD or server.cluster != task.cluster)

    def _bft_wait(self, now: float) -> float:
        p = self.lc["bft_period_s"]
        return p - (now % p)

    def _bft_ok(self) -> bool:
        return self.lc["bft_faulty"] <= (self.lc["bft_replicas"] - 1) // 3

    # ------------------------------------------------------------ public API
    def expected_delay(self, task, server, now: float) -> float:
        cap = self._batch_cap(task.cluster, now)
        poa_mean = self.lc["poa_median_s"] * np.exp(self.lc["poa_sigma"] ** 2 / 2)
        d = cap / 2 + poa_mean
        if self._needs_bft(task, server):
            bft_mean = self.lc["bft_median_s"] * np.exp(self.lc["bft_sigma"] ** 2 / 2)
            d += self._bft_wait(now) + (bft_mean if self._bft_ok()
                                        else self.max_retries * self._retry_cost())
        return float(d * self.cc["delay_scale"])

    @property
    def max_retries(self) -> int:
        return int(self.cc.get("max_retries", 3))

    def _retry_cost(self) -> float:
        return self.lc["bft_timeout_s"] + self.lc["bft_period_s"]

    def sample_delay(self, task, server, now: float) -> tuple[float, bool]:
        """Realised delay and whether confirmation failed (BFT retries exhausted)."""
        self._times.setdefault(task.cluster, []).append(now)
        if self.cc.get("distribution", "sampled") == "fixed":
            d = self.expected_delay(task, server, now) / self.cc["delay_scale"]
            timed_out = self._needs_bft(task, server) and not self._bft_ok()
        else:
            d = self.rng.uniform(0.0, self._batch_cap(task.cluster, now))
            d += self.lc["poa_median_s"] * self.rng.lognormal(0.0, self.lc["poa_sigma"])
            timed_out = False
            if self._needs_bft(task, server):
                d += self._bft_wait(now)
                if self._bft_ok():
                    d += self.lc["bft_median_s"] * self.rng.lognormal(0.0, self.lc["bft_sigma"])
                else:
                    d += self.max_retries * self._retry_cost()
                    timed_out = True
        if timed_out:
            self.timeouts += 1
        return float(d * self.cc["delay_scale"]), timed_out
