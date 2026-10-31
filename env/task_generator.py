"""Workload generator (M2).

Paper-aligned parts (Sec. IV-B2, Table IV): class shares 20/50/30 and
relative deadline bands URLLC U[5,15] s, eMBB U[30,120] s, mMTC U[120,600] s.

ASSUMPTIONS (paper derives these from Brasov air-quality traces, which we do
not have): Poisson arrivals at a configured rate over a fixed horizon, a
uniform home cluster, and uniform CPU/memory/payload ranges per class.
"""

from __future__ import annotations

import numpy as np

from .task import Task

CLASSES = ("URLLC", "eMBB", "mMTC")


class TaskGenerator:

    def __init__(self, workload_cfg: dict, seed: int):
        self.cfg = workload_cfg
        self.rng = np.random.default_rng(seed)

    def _uniform(self, table: str, cls: str) -> float:
        lo, hi = self.cfg[table][cls]
        return float(self.rng.uniform(lo, hi))

    def generate_task(self, task_id: int, arrival_time: float) -> Task:
        shares = self.cfg["class_shares"]
        cls = str(self.rng.choice(CLASSES, p=[shares[c] for c in CLASSES]))
        return Task(
            id=task_id,
            arrival_time=arrival_time,
            deadline=arrival_time + self._uniform("deadline_bands_s", cls),
            cluster=int(self.rng.integers(0, self.cfg["num_clusters"])),
            service_class=cls,
            cpu_cycles=self._uniform("cpu_cycles", cls),
            memory=self._uniform("memory_mb", cls),
            payload=self._uniform("payload_bits", cls),
            priority=float(self.cfg["class_weight"][cls]),
        )

    def generate_episode(self, num_tasks: int | None = None) -> list[Task]:
        """Poisson arrivals at the regime rate. If num_tasks is given the
        episode is cut to that many tasks (used for short training episodes)."""
        rate = self.cfg["load_regimes_tasks_per_s"][self.cfg["regime"]]
        n = num_tasks if num_tasks is not None else int(rate * self.cfg["horizon_s"])
        gaps = self.rng.exponential(1.0 / rate, size=n)
        arrivals = np.cumsum(gaps)
        return [self.generate_task(i, float(t)) for i, t in enumerate(arrivals)]
