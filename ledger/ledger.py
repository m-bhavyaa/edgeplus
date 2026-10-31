"""Two-tier blockchain-lite ledger SIMULATOR (M12, paper Sec. III-H, III-M).

This is a research simulator, not a blockchain. What it models:

Edge tier (per cluster, PoA):
  * log tuple per executed task (Eq. 18), added when the task FINISHES
  * partial blocks linked by hash; h = BLAKE2b(SHA3-256(block)) (Eq. 19-20)
  * adaptive block size S_c(t) = S_min + (rho_c/rho_max + lam_c/lam_max)(S_max - S_min),
    clipped to [S_min, S_max] (Eq. 21); a block also seals after block_timeout_s
  * PoA validation: proposer must be a cluster authority and the hash chain must
    verify (Eq. 22). Validation delay ~ LogNormal(median = poa_median_s).
Cloud tier (BFT):
  * every bft_period_s the latest validated hash of each cluster is aggregated in
    ascending cluster order (Eq. 24) and "signed" (Eq. 25 is modelled by a hash,
    Ed25519 is NOT implemented). With n replicas, the round commits iff the number
    of faulty replicas <= f = (n-1)//3; otherwise it times out (view change).
Feedback (Eq. 14-16, 28-29):
  * reputation rho_s = EMA(1[on-time] - kappa*1[violation]), initial 1.0, updated
    only from records inside VALIDATED blocks
  * debt d_c = max(0, mean_theta - theta_c) / mean_theta  (normalised; ASSUMPTION:
    theta_c = committed on-time completions of cluster c per second)
  * phi(rho) = max(0, rho_th - rho)  (hinge, Eq. 16)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

import numpy as np


def block_hash(payload: dict) -> str:
    """Eq. 20: BLAKE2b(SHA3-256(serialised block))."""
    raw = json.dumps(payload, sort_keys=True, default=float).encode()
    return hashlib.blake2b(hashlib.sha3_256(raw).digest()).hexdigest()


@dataclass
class PartialBlock:
    cluster: int
    index: int
    records: list
    prev_hash: str
    proposer: str
    sealed_at: float
    hash: str = ""
    validated_at: float | None = None

    def payload(self) -> dict:
        return {"cluster": self.cluster, "index": self.index, "records": self.records,
                "prev": self.prev_hash, "proposer": self.proposer}


@dataclass
class EdgeChain:
    cluster: int
    authorities: list
    blocks: list = field(default_factory=list)
    pending: list = field(default_factory=list)
    pending_since: float | None = None

    @property
    def head_hash(self) -> str:
        return self.blocks[-1].hash if self.blocks else "genesis"


class Ledger:

    def __init__(self, cfg: dict, num_clusters: int):
        self.cfg = cfg
        self.num_clusters = num_clusters
        self.reset()

    # ----------------------------------------------------------------- state
    def reset(self, seed: int = 0) -> None:
        self.rng = np.random.default_rng(seed)
        n = self.cfg["authorities_per_cluster"]
        self.chains = {c: EdgeChain(c, [f"auth-{c}-{k}" for k in range(n)])
                       for c in range(self.num_clusters)}
        self.rep: dict[int, float] = {}
        self.ontime_by_cluster = np.zeros(self.num_clusters)
        self.now = 0.0
        self.next_bft = self.cfg["bft_period_s"]
        self.global_blocks: list[dict] = []
        self.stats = {"records": 0, "blocks": 0, "rejected_blocks": 0, "bft_rounds": 0,
                      "bft_timeouts": 0, "poa_delays": [], "bft_delays": []}
        self._write_times = {c: [] for c in range(self.num_clusters)}

    # ------------------------------------------------------------- edge tier
    def block_size(self, cluster: int, rho: float = 0.5) -> int:
        """Eq. 21 with rho_max = 1 and lam_max = 10 records/s (ASSUMPTION)."""
        lam = self.write_rate(cluster)
        smin, smax = self.cfg["block_min"], self.cfg["block_max"]
        frac = min(1.0, rho / 1.0 + lam / 10.0)
        return int(round(smin + frac * (smax - smin)))

    def write_rate(self, cluster: int, window: float = 10.0) -> float:
        ts = [t for t in self._write_times[cluster] if t > self.now - window]
        self._write_times[cluster] = ts
        return len(ts) / window

    def record(self, log: dict) -> None:
        """Receive an Eq. 18 log tuple (called by the simulator at t_end)."""
        c = log["cluster"] if log["cluster"] >= 0 else log["origin"]
        ch = self.chains[c]
        if not ch.pending:
            ch.pending_since = log["t_end"]
        ch.pending.append(log)
        self._write_times[c].append(log["t_end"])
        self.stats["records"] += 1
        if len(ch.pending) >= self.block_size(c):
            self._seal(ch, log["t_end"])

    def _seal(self, ch: EdgeChain, t: float) -> None:
        proposer = ch.authorities[len(ch.blocks) % len(ch.authorities)]  # rotating leader
        blk = PartialBlock(ch.cluster, len(ch.blocks), ch.pending, ch.head_hash, proposer, t)
        blk.hash = block_hash(blk.payload())
        ch.pending, ch.pending_since = [], None
        self.submit_block(blk)

    def validate_block(self, blk: PartialBlock) -> bool:
        """Eq. 22: proposer is an authority of the cluster AND hashes verify."""
        ch = self.chains[blk.cluster]
        return (blk.proposer in ch.authorities and blk.prev_hash == ch.head_hash
                and blk.index == len(ch.blocks) and blk.hash == block_hash(blk.payload()))

    def submit_block(self, blk: PartialBlock) -> bool:
        if not self.validate_block(blk):
            self.stats["rejected_blocks"] += 1
            return False
        ch = self.chains[blk.cluster]
        size_factor = (len(ch.authorities) + len(blk.records)) / 20.0
        d = self.poa_delay_sample() * size_factor
        blk.validated_at = blk.sealed_at + d
        ch.blocks.append(blk)
        self.stats["blocks"] += 1
        self.stats["poa_delays"].append(d)
        for r in blk.records:
            self._update_feedback(r)
        return True

    def poa_delay_sample(self) -> float:
        return float(self.cfg["poa_median_s"] * self.rng.lognormal(0.0, self.cfg["poa_sigma"]))

    # ------------------------------------------------------------ cloud tier
    def bft_quorum_ok(self) -> bool:
        n, faulty = self.cfg["bft_replicas"], self.cfg["bft_faulty"]
        return faulty <= (n - 1) // 3

    def _bft_round(self, t: float) -> None:
        self.stats["bft_rounds"] += 1
        if not self.bft_quorum_ok():
            self.stats["bft_timeouts"] += 1
            return
        hashes = [(c, self.chains[c].head_hash) for c in sorted(self.chains)]  # Eq. 24
        full = {"round": len(self.global_blocks), "hashes": hashes}
        full["signature"] = block_hash({"signer": "bft-primary", **full})     # stands in for Eq. 25
        d = float(self.cfg["bft_median_s"] * self.rng.lognormal(0.0, self.cfg["bft_sigma"]))
        full["finalized_at"] = t + d
        self.stats["bft_delays"].append(d)
        self.global_blocks.append(full)

    def verify_global(self, full: dict) -> bool:
        ids = [c for c, _ in full["hashes"]]
        return len(ids) == self.num_clusters and all(a < b for a, b in zip(ids, ids[1:]))

    def advance(self, now: float) -> None:
        self.now = now
        for ch in self.chains.values():
            if ch.pending and now - ch.pending_since >= self.cfg["block_timeout_s"]:
                self._seal(ch, ch.pending_since + self.cfg["block_timeout_s"])
        while self.next_bft <= now:
            self._bft_round(self.next_bft)
            self.next_bft += self.cfg["bft_period_s"]

    # -------------------------------------------------------------- feedback
    def _update_feedback(self, r: dict) -> None:
        a, kappa = self.cfg["rep_ema_alpha"], self.cfg["rep_kappa"]
        x = 1.0 if r["on_time"] else -kappa
        s = r["server"]
        self.rep[s] = (1 - a) * self.rep.get(s, 1.0) + a * x
        if r["on_time"]:
            c = r["cluster"] if r["cluster"] >= 0 else r["origin"]
            self.ontime_by_cluster[c] += 1

    def reputation(self, server_id: int) -> float:
        return float(np.clip(self.rep.get(server_id, 1.0), 0.0, 1.0))

    def reputation_penalty(self, server_id: int) -> float:
        return max(0.0, self.cfg["rep_threshold"] - self.reputation(server_id))

    def debt(self, cluster: int) -> float:
        if cluster < 0 or self.now <= 0:
            return 0.0
        theta = self.ontime_by_cluster / self.now
        mean = theta.mean()
        return 0.0 if mean <= 0 else float(max(0.0, mean - theta[cluster]) / mean)
