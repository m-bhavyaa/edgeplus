import numpy as np

from .task import Task
from .server import Server
from .topology import Topology


class EdgePlusEnv:

    def __init__(self, servers):

        self.servers = servers
        self.topology = Topology()

        self.current_task = None
        self.time = 0.0

    def reset(self):

        self.time = 0.0
        self.current_task = None

        for server in self.servers:
            server.queue_time = 0.0
            server.memory_used = 0.0
            server.energy_used = 0.0

        return self.get_state()

    def set_task(self, task):

        self.current_task = task
        self.time = task.arrival_time

    # --------------------------------------------------
    # TOPOLOGY
    # --------------------------------------------------

    def candidate_servers(self, task):

        local_servers = [
            server
            for server in self.servers
            if server.cluster == task.cluster
        ]

        neighbor_clusters = self.topology.get_neighbors(
            task.cluster
        )

        neighbor_servers = [
            server
            for server in self.servers
            if server.cluster in neighbor_clusters
        ]

        return local_servers + neighbor_servers

    # --------------------------------------------------
    # LATENCY
    # --------------------------------------------------

    def transmission_latency(self, task, server):

        rate = max(server.bandwidth, 1e-9)

        return task.payload / rate

    def movement_latency(self, task, server):

        if server.cluster == task.cluster:
            return 0.0

        if self.topology.are_neighbors(
            task.cluster,
            server.cluster
        ):
            distance = self.topology.distance(
                task.cluster,
                server.cluster
            )

            return 0.01 * distance

        return 0.0

    def processing_latency(self, task, server):

        return task.cpu_cycles / server.cpu_rate

    def queue_latency(self, server):

        return server.queue_time

    def total_latency(self, task, server):

        transmission = self.transmission_latency(
            task,
            server
        )

        movement = self.movement_latency(
            task,
            server
        )

        queue = self.queue_latency(server)

        processing = self.processing_latency(
            task,
            server
        )

        return (
            transmission
            + movement
            + queue
            + processing
        )

    # --------------------------------------------------
    # FEASIBILITY
    # --------------------------------------------------

    def is_feasible(self, task, server):

        latency = self.total_latency(
            task,
            server
        )

        deadline_ok = (
            task.arrival_time + latency
            <= task.deadline
        )

        memory_ok = (
            server.available_memory
            >= task.memory
        )

        return deadline_ok and memory_ok

    def get_action_mask(self):

        if self.current_task is None:
            raise ValueError(
                "No task has been assigned."
            )

        mask = []

        for server in self.servers:

            if server in self.candidate_servers(
                self.current_task
            ):
                feasible = self.is_feasible(
                    self.current_task,
                    server
                )
            else:
                feasible = False

            mask.append(int(feasible))

        return np.array(
            mask,
            dtype=np.int8
        )

    # --------------------------------------------------
    # EXECUTION
    # --------------------------------------------------

    def execute(self, server_id):

        if self.current_task is None:
            raise ValueError(
                "No task has been assigned."
            )

        task = self.current_task
        server = self.servers[server_id]

        if not self.is_feasible(task, server):

            return {
                "success": False,
                "latency": None,
                "reward": -10.0,
                "server_id": server_id
            }

        latency = self.total_latency(
            task,
            server
        )

        processing = self.processing_latency(
            task,
            server
        )

        server.queue_time += processing
        server.memory_used += task.memory

        reward = 10.0 - latency

        return {
            "success": True,
            "latency": latency,
            "reward": reward,
            "server_id": server_id
        }

    # --------------------------------------------------
    # STATE
    # --------------------------------------------------

    def get_state(self):

        if self.current_task is None:
            return None

        task = self.current_task

        state = [
            task.cpu_cycles,
            task.memory,
            task.payload,
            task.deadline_slack,
            task.cluster
        ]

        for server in self.servers:

            state.extend([
                server.cpu_rate,
                server.available_memory,
                server.bandwidth,
                server.queue_time
            ])

        return np.array(
            state,
            dtype=np.float32
        )