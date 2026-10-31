"""Per-sensor battery model (energy-preservation extension, NOT in the paper).

Each IoT sensor j has
    capacity B (J), level b_j(t), solar harvest h(t) = h_peak * max(0, sin(2*pi*t / P_day)),
    a sensing cost E_sense per reading, and an upload cost E_up = P_tx * L_air
    (radio airtime only: payload / (bandwidth * gain); cloud backhaul is wired, so the
    sensor does not pay for it).
A sensor with b_j < E_sense is DEAD: it cannot produce readings until it recharges.

Long-term preservation uses a Lyapunov virtual energy queue (Neely; LODCO, Mao et al. 2016):
    Z_j <- max(Z_j + E_spent - e_bar, 0)
where e_bar is the sustainable energy per reading. A large Z_j means "this sensor
spends faster than it can afford". Policies use it as a price on upload energy.

Time is compressed: one simulated "day" lasts P_day seconds (default = one episode).
"""

from __future__ import annotations

import numpy as np


class SensorField:

    def __init__(self, cfg: dict, num_clusters: int):
        self.cfg = cfg
        self.n = cfg["per_cluster"] * num_clusters
        self.cluster = np.repeat(np.arange(num_clusters), cfg["per_cluster"])
        self.reset(0)

    def reset(self, seed: int) -> None:
        rng = np.random.default_rng(seed + 104729)
        lo, hi = self.cfg["initial_fraction"]
        self.B = self.cfg["battery_j"]
        self.b = rng.uniform(lo, hi, self.n) * self.B
        self.Z = np.zeros(self.n)
        self.t = 0.0
        self.death_time = np.full(self.n, np.nan)   # first time each sensor died
        self.spent = np.zeros(self.n)
        self.harvested = np.zeros(self.n)
        self.dropped = 0

    # ---------------------------------------------------------------- dynamics
    def harvest_power(self, t: float) -> float:
        return self.cfg["harvest_peak_w"] * max(0.0, np.sin(2 * np.pi * t / self.cfg["day_period_s"]))

    def advance(self, now: float) -> None:
        """Recharge every sensor for the elapsed interval (midpoint rule)."""
        dt = now - self.t
        if dt <= 0:
            return
        e = self.harvest_power(self.t + dt / 2) * dt
        room = self.B - self.b
        gained = np.minimum(e, room)
        self.b += gained
        self.harvested += gained
        self.t = now

    def alive(self, j: int) -> bool:
        return self.b[j] >= self.cfg["sensing_j"]

    def upload_energy(self, task, server) -> float:
        airtime = task.payload / (server.bandwidth * max(server.channel_gain, 1e-9))
        return self.cfg["p_tx_w"] * airtime

    def can_afford(self, j: int, e_up: float) -> bool:
        return self.b[j] >= e_up

    def spend(self, j: int, e: float, now: float) -> None:
        self.b[j] = max(0.0, self.b[j] - e)
        self.spent[j] += e
        if not self.alive(j) and np.isnan(self.death_time[j]):
            self.death_time[j] = now

    def update_queue(self, j: int, e_spent: float) -> None:
        self.Z[j] = max(0.0, self.Z[j] + e_spent - self.cfg["budget_per_reading_j"])

    # ----------------------------------------------------------------- metrics
    def stats(self) -> dict:
        frac = self.b / self.B
        died = ~np.isnan(self.death_time)
        jain = frac.sum() ** 2 / (self.n * (frac ** 2).sum()) if frac.any() else 0.0
        return {"sensor_dead_end_frac": float(np.mean(~(self.b >= self.cfg["sensing_j"]))),
                "sensor_ever_died_frac": float(died.mean()),
                "sensor_first_death_s": float(np.nanmin(self.death_time)) if died.any() else float("nan"),
                "sensor_battery_mean_frac": float(frac.mean()),
                "sensor_battery_min_frac": float(frac.min()),
                "sensor_battery_jain": float(jain),
                "sensor_energy_spent_j": float(self.spent.sum()),
                "sensor_readings_dropped": int(self.dropped)}
