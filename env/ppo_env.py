"""Gymnasium wrapper around EdgePlusEnv for single-agent PPO (M7) and MaskablePPO (M8).

- Each reset() draws a NEW workload from a seed stream (fixes audit D9).
  Pass ``workload_seed`` in reset(options=...) to replay a fixed evaluation workload.
- If the offered task has no feasible server, the wrapper rejects it explicitly
  and moves to the next task; the agent is never asked to act on an all-false mask.
  The rejection is reported in ``info["skipped"]`` so evaluators can count it.
"""

from __future__ import annotations

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from .edge_env import EdgePlusEnv
from .task_generator import TaskGenerator


class PPOEdgeEnv(gym.Env):

    def __init__(self, cfg: dict, num_tasks: int | None = None, seed: int = 0,
                 ledger=None, consensus=None):
        super().__init__()
        self.cfg = cfg
        self.num_tasks = num_tasks
        self.base_seed = seed
        self.episode = 0
        self.core = EdgePlusEnv(cfg, seed=seed, ledger=ledger, consensus=consensus)
        self.observation_space = spaces.Box(-np.inf, np.inf, (self.core.state_dim,), np.float32)
        self.action_space = spaces.Discrete(len(self.core.servers))
        self.tasks, self.idx = [], 0
        self.skipped: list[dict] = []

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        options = options or {}
        wseed = options.get("workload_seed", self.base_seed + self.episode)
        self.episode += 1
        self.core.reset(seed=wseed)
        self.tasks = TaskGenerator(self.cfg["workload"], wseed).generate_episode(self.num_tasks)
        self.idx = 0
        self.skipped = []
        self._load_next()
        return self.core.get_state(), {"skipped": self._drain_skipped()}

    def _load_next(self) -> bool:
        """Advance to the next task with >=1 feasible server; reject the others."""
        while self.idx < len(self.tasks):
            self.core.set_task(self.tasks[self.idx])
            if self.core.get_action_mask().any():
                return True
            self.skipped.append(self.core.reject())
            self.idx += 1
        return False

    def _drain_skipped(self) -> list[dict]:
        out, self.skipped = self.skipped, []
        return out

    def action_masks(self) -> np.ndarray:
        return self.core.get_action_mask()

    def step(self, action):
        result = self.core.execute(int(action))
        self.idx += 1
        terminated = not self._load_next()
        obs = (np.zeros(self.observation_space.shape, np.float32) if terminated
               else self.core.get_state())
        skipped = self._drain_skipped()
        reward = result["reward"] + sum(r["reward"] for r in skipped)
        return obs, reward, terminated, False, {"result": result, "skipped": skipped}
