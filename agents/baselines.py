"""Simple policies with a common interface.

A policy is any object with
    act(core, mask) -> int     # server id; called only when mask.any() is True
    reset(core)                # optional, start of an evaluation episode
Zero-feasible tasks are rejected by the evaluator before act() is called, so
every policy is scored on exactly the same rejection rule.
"""

from __future__ import annotations

import numpy as np


class RandomFeasible:
    """M6: uniform over feasible servers."""
    name = "m6_random"

    def __init__(self, seed: int = 0):
        self.seed = seed

    def reset(self, core):
        self.rng = np.random.default_rng(self.seed + core.seed)

    def act(self, core, mask):
        return int(self.rng.choice(np.flatnonzero(mask)))


class GreedyMinLatency:
    """Sanity baseline: feasible server with the smallest predicted latency."""
    name = "greedy"

    def reset(self, core):
        pass

    def act(self, core, mask):
        t = core.current_task
        ids = np.flatnonzero(mask)
        return int(ids[np.argmin([core.total_latency(t, core.servers[i]) for i in ids])])


class SB3Policy:
    """M7 (PPO, unmasked) or M8 (MaskablePPO) checkpoint."""

    def __init__(self, path: str, masked: bool, name: str):
        self.masked, self.name = masked, name
        if masked:
            from sb3_contrib import MaskablePPO
            self.model = MaskablePPO.load(path, device="cpu")
        else:
            from stable_baselines3 import PPO
            self.model = PPO.load(path, device="cpu")

    def reset(self, core):
        pass

    def act(self, core, mask):
        obs = core.get_state()
        if self.masked:
            a, _ = self.model.predict(obs, action_masks=mask, deterministic=True)
        else:
            a, _ = self.model.predict(obs, deterministic=True)  # may pick an infeasible server
        return int(a)


class LyapunovGreedy:
    """Energy-aware greedy (drift-plus-penalty, extension):
        argmin_s  L_pred(s) / slack  +  V * Z_j * E_up(s) / e_ref
    With V = 0 this is GreedyMinLatency up to tie-breaking (latency is normalised)."""

    def __init__(self, V: float = 1.0, name: str = "greedy_lyapunov"):
        self.V, self.name = V, name

    def reset(self, core):
        pass

    def act(self, core, mask):
        t = core.current_task
        slack = max(t.deadline - core.time, 1e-6)
        ids = np.flatnonzero(mask)
        score = [core.total_latency(t, core.servers[i]) / slack
                 + self.V * core.lyapunov_price(t, core.servers[i]) for i in ids]
        return int(ids[np.argmin(score)])
