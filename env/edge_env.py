"""EdgePlus scheduling simulator core (M3-M5, plus hooks for M12/M14).

One task is offered at a time (event-driven by arrival). For the offered task
the simulator can (1) list why each server is or is not feasible, (2) build the
action mask, and (3) execute an assignment or an explicit rejection.

Timing model (fixes audit D3):
    ready  = now + L_consensus + L_tx + L_move     (data at server)
    start  = max(ready, server backlog end)        (FIFO, non-preemptive)
    finish = start + L_proc_realised
    L_queue = start - ready,  latency = finish - arrival
The mask uses the *expected* processing time k/f. The executor uses the
realised time k/f * slowdown * noise, so an admitted task can still be late
(audit D16). The scheduler sees the true backlog of jobs already queued
(documented simplification).

Every offered task ends with exactly one outcome:
    on_time | late | rejected_no_feasible | rejected_infeasible_action
"""

from __future__ import annotations

import heapq

import numpy as np

from .server import CLOUD, MOBILE, STATIONARY, Server, build_servers
from .task import Task
from .topology import Topology

CLASSES = ("URLLC", "eMBB", "mMTC")
CONSTRAINTS = ("routing", "slice", "memory", "energy", "deadline", "reputation")
OUTCOMES = ("on_time", "late", "rejected_no_feasible", "rejected_infeasible_action")


class EdgePlusEnv:

    def __init__(self, cfg: dict, seed: int = 0, ledger=None, consensus=None):
        self.cfg = cfg
        self.sim = cfg["simulator"]
        self.topology = Topology()
        self.servers: list[Server] = build_servers(cfg["servers"], cfg["workload"]["num_clusters"])
        self.ledger = ledger          # ledger.Ledger or None (M12)
        self.consensus = consensus    # ledger.ConsensusDelayModel or None (M14)
        self.seed = seed
        self.reset()

    # ------------------------------------------------------------------ state
    def reset(self, seed: int | None = None) -> None:
        if seed is not None:
            self.seed = seed
        self.rng = np.random.default_rng(self.seed)
        self.time = 0.0
        self.current_task: Task | None = None
        self._pending_logs: list = []   # (finish_time, seq, log tuple) for the ledger
        self._seq = 0
        for s in self.servers:
            s.active_jobs.clear()
            s.energy_used = 0.0
        if self.ledger is not None:
            self.ledger.reset(self.seed)
        if self.consensus is not None:
            self.consensus.reset(self.seed)

    def advance_time(self, new_time: float) -> None:
        if new_time < self.time:
            raise ValueError("Simulation time cannot move backwards.")
        self.time = new_time
        for s in self.servers:
            s.release_completed_jobs(new_time)
        # Ledger receives a task's log tuple only once the task has finished (Eq. 18 has t_end).
        while self._pending_logs and self._pending_logs[0][0] <= new_time:
            _, _, log = heapq.heappop(self._pending_logs)
            self.ledger.record(log)
        if self.ledger is not None:
            self.ledger.advance(new_time)

    def set_task(self, task: Task) -> None:
        self.advance_time(task.arrival_time)
        self.current_task = task

    # ---------------------------------------------------------------- routing
    def routing_region(self, task: Task, server: Server) -> int | None:
        """Paper order (Sec. III-C1): 0 stationary in c(i), 1 mobile in c(i),
        2 mobile in N(c(i)), 3 cloud. None = not routable.
        'legacy' routing (pre-audit behaviour): 0 any local, 1 any neighbour."""
        local = server.cluster == task.cluster
        neigh = server.cluster >= 0 and self.topology.are_neighbors(task.cluster, server.cluster)
        if self.sim["routing"] == "legacy":
            return 0 if local else (1 if neigh else None)
        if server.kind == CLOUD:
            return 3
        if local:
            return 0 if server.kind == STATIONARY else 1
        if neigh and server.kind == MOBILE:
            return 2
        return None

    def routing_feasible(self, task, server) -> bool:
        return self.routing_region(task, server) is not None

    # ---------------------------------------------------------------- latency
    def transmission_latency(self, task, server) -> float:
        tx = task.payload / (server.bandwidth * max(server.channel_gain, 1e-9))
        if server.kind == CLOUD:
            tx += self.cfg["servers"]["cloud"]["backhaul_s"]
        return tx

    def movement_latency(self, task, server) -> float:
        """Mobiles drive from their home cluster to the task's cluster
        (straight line; CBS-D* Lite path planning is not modelled)."""
        if server.kind != MOBILE or server.cluster == task.cluster:
            return 0.0
        metres = self.topology.distance(task.cluster, server.cluster) \
            * self.cfg["servers"]["km_per_grid_unit"] * 1000.0
        return metres / server.speed_mps

    def processing_latency(self, task, server) -> float:
        """Expected processing time k/f (Eq. 32)."""
        return task.cpu_cycles / server.cpu_rate

    def expected_consensus_delay(self, task, server) -> float:
        """Consensus delay the *mask* accounts for (only in mask_aware mode)."""
        if self.consensus is None or self.cfg["consensus"]["mode"] != "mask_aware":
            return 0.0
        return self.consensus.expected_delay(task, server, self.time)

    def latency_components(self, task, server) -> dict:
        cons = self.expected_consensus_delay(task, server)
        tx = self.transmission_latency(task, server)
        move = self.movement_latency(task, server)
        ready = self.time + cons + tx + move
        queue = max(0.0, server.last_finish_time() - ready)
        return {"consensus": cons, "transmission": tx, "movement": move,
                "queue": queue, "processing": self.processing_latency(task, server)}

    def total_latency(self, task, server) -> float:
        return sum(self.latency_components(task, server).values())

    def queue_latency(self, server) -> float:
        return server.backlog(self.time)

    # ------------------------------------------------------------ constraints
    def memory_feasible(self, task, server) -> bool:
        return server.available_memory >= task.memory

    def energy_required(self, task, server, tx=None, move=None) -> float:
        """Eq. 2: E = P_tx L_tx + chi * distance + kappa * k."""
        e = self.sim["energy"]
        tx = self.transmission_latency(task, server) if tx is None else tx
        move = self.movement_latency(task, server) if move is None else move
        return e["p_tx_w"] * tx + e["chi_j_per_m"] * move * server.speed_mps \
            + e["kappa_j_per_cycle"] * task.cpu_cycles

    def energy_feasible(self, task, server) -> bool:
        if server.kind != MOBILE:          # Eq. 3 constrains mobiles only
            return True
        return server.available_energy >= self.energy_required(task, server)

    def slice_load(self, cluster: int, service_class: str) -> float:
        """Outstanding processing seconds of one class in one cluster (Eq. 4, compute part)."""
        total = 0.0
        for s in self.servers:
            if s.cluster != cluster:
                continue
            for j in s.active_jobs:
                if j["service_class"] == service_class:
                    total += j["finish_time"] - max(self.time, j["start_time"])
        return total

    def slice_feasible(self, task, server) -> bool:
        if server.kind == CLOUD:           # slices are reserved per edge cluster
            return True
        budget = self.sim["slice_compute_budget_s"][task.service_class]
        return self.slice_load(server.cluster, task.service_class) \
            + self.processing_latency(task, server) <= budget

    def deadline_feasible(self, task, server) -> bool:
        scope = self.sim["deadline_mask"]  # all | urllc | none
        if scope == "none" or (scope == "urllc" and task.service_class != "URLLC"):
            return True
        return task.arrival_time + self.total_latency(task, server) <= task.deadline

    def reputation_feasible(self, task, server) -> bool:
        """URLLC quarantine of low-reputation servers (Sec. III-H)."""
        lc = self.cfg["ledger"]
        if self.ledger is None or not lc["quarantine"] or task.service_class != "URLLC":
            return True
        return self.ledger.reputation(server.id) >= lc["urllc_quarantine_threshold"]

    def feasibility_reasons(self, task, server) -> dict:
        r = {"routing": self.routing_feasible(task, server)}
        r["slice"] = self.slice_feasible(task, server)
        r["memory"] = self.memory_feasible(task, server)
        r["energy"] = self.energy_feasible(task, server)
        r["deadline"] = self.deadline_feasible(task, server)
        r["reputation"] = self.reputation_feasible(task, server)
        r["feasible"] = all(r[c] for c in CONSTRAINTS)
        return r

    def is_feasible(self, task, server) -> bool:
        return self.feasibility_reasons(task, server)["feasible"]

    def get_action_mask(self) -> np.ndarray:
        if self.current_task is None:
            raise ValueError("No task has been assigned.")
        return np.array([self.is_feasible(self.current_task, s) for s in self.servers], dtype=bool)

    # -------------------------------------------------------------- execution
    def _reward(self, task, outcome, latency=0.0, energy=0.0, server=None) -> float:
        """Eq. 7 plus ledger shaping Eq. 15/29."""
        rw = self.cfg["reward"]
        w = task.priority
        if outcome == "on_time":
            r = rw["eta1"] * w
        else:
            r = -rw["eta2"] * w
        if outcome == "rejected_infeasible_action":
            r -= rw["infeasible_penalty"]
        if server is not None:
            budget = task.deadline - task.arrival_time
            r -= rw["eta3"] * min(latency / budget, 3.0)
            r -= rw["eta4"] * energy / rw["energy_ref_j"]
            r -= rw["eta5"] * (server.kind == CLOUD)
            if self.ledger is not None:
                r -= rw["eta6"] * self.ledger.reputation_penalty(server.id)
                r -= rw["eta7"] * self.ledger.debt(server.cluster)
        return float(r)

    def _base_result(self, task, outcome, server_id=None) -> dict:
        return {"task_id": task.id, "service_class": task.service_class,
                "cluster": task.cluster, "arrival_time": task.arrival_time,
                "deadline": task.deadline, "outcome": outcome, "server_id": server_id,
                "success": outcome == "on_time", "executed": outcome in ("on_time", "late")}

    def reject(self) -> dict:
        """Explicit outcome for a task with no feasible server."""
        task = self.current_task
        res = self._base_result(task, "rejected_no_feasible")
        res["reward"] = self._reward(task, "rejected_no_feasible")
        return res

    def execute(self, server_id: int) -> dict:
        task = self.current_task
        if task is None:
            raise ValueError("No task has been assigned.")
        server = self.servers[server_id]
        if not self.is_feasible(task, server):
            res = self._base_result(task, "rejected_infeasible_action", server_id)
            res["reward"] = self._reward(task, "rejected_infeasible_action")
            return res

        mode = self.cfg["consensus"]["mode"]
        cons, timed_out = 0.0, False
        if self.consensus is not None and mode in ("mask_aware", "report_only"):
            cons, timed_out = self.consensus.sample_delay(task, server, self.time)
        tx = self.transmission_latency(task, server)
        move = self.movement_latency(task, server)
        ready = self.time + cons + tx + move
        start = max(ready, server.last_finish_time())
        cv = self.sim["service_noise_cv"]
        noise = float(self.rng.lognormal(-0.5 * np.log1p(cv ** 2), np.sqrt(np.log1p(cv ** 2)))) \
            if cv > 0 else 1.0
        proc = self.processing_latency(task, server) * server.slowdown * noise
        finish = start + proc
        latency = finish - task.arrival_time
        outcome = "on_time" if finish <= task.deadline else "late"
        energy = self.energy_required(task, server, tx, move)

        server.energy_used += energy
        server.add_job(task.id, task.service_class, task.memory, start, finish)
        if self.ledger is not None:
            log = {"task": task.id, "cluster": server.cluster, "origin": task.cluster, "server": server.id,
                   "class": task.service_class, "deadline": task.deadline,
                   "t_arrival": task.arrival_time, "t_end": finish,
                   "on_time": outcome == "on_time", "energy": energy}
            heapq.heappush(self._pending_logs, (finish, self._seq, log))
            self._seq += 1

        res = self._base_result(task, outcome, server_id)
        res.update({"server_kind": server.kind, "server_cluster": server.cluster,
                    "routing_tier": self.routing_region(task, server),
                    "latency": latency, "consensus": cons, "consensus_timeout": timed_out,
                    "transmission": tx, "movement": move, "queue": start - ready,
                    "processing": proc, "energy": energy, "start_time": start,
                    "finish_time": finish})
        res["reward"] = self._reward(task, outcome, latency, energy, server)
        return res

    # ------------------------------------------------------------ observation
    def cluster_load(self, cluster: int, ref_backlog_s: float = 10.0) -> float:
        """Utilisation proxy rho_c in [0,1]: mean server backlog / ref, clipped."""
        ss = [s for s in self.servers if s.cluster == cluster]
        return float(np.mean([min(1.0, s.backlog(self.time) / ref_backlog_s) for s in ss]))

    def task_features(self, task: Task) -> list[float]:
        onehot = [float(task.service_class == c) for c in CLASSES]
        return onehot + [task.cpu_cycles / 1e10, task.memory / 2048.0, task.payload / 2e7,
                         (task.deadline - self.time) / 600.0]

    def server_features(self, task: Task, server: Server) -> list[float]:
        """Scaled per-server features (fixes audit D8). Includes predicted
        latency relative to the task's remaining slack."""
        slack = max(task.deadline - self.time, 1e-6)
        routable = self.routing_feasible(task, server)
        pred = self.total_latency(task, server) if routable else 0.0
        rep = self.ledger.reputation(server.id) if self.ledger is not None else 1.0
        energy = 1.0 if server.kind != MOBILE else server.available_energy / server.energy_budget
        return [float(routable), float(server.kind == MOBILE), float(server.kind == CLOUD),
                min(server.backlog(self.time) / 60.0, 5.0),
                server.available_memory / server.memory_capacity, energy,
                server.cpu_rate / 1e10, min(pred / slack, 5.0), rep]

    def get_state(self) -> np.ndarray:
        task = self.current_task
        feats = self.task_features(task)
        for s in self.servers:
            feats.extend(self.server_features(task, s))
        return np.array(feats, dtype=np.float32)

    @property
    def state_dim(self) -> int:
        return 7 + 9 * len(self.servers)
