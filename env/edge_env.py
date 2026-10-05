import numpy as np

from .task import Task
from .server import Server


class EdgePlusEnv:

    def __init__(self, servers):
        self.servers = servers
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

    def transmission_latency(self, task, server):
        rate = max(server.bandwidth, 1e-9)
        return task.payload / rate

    def processing_latency(self, task, server):
        return task.cpu_cycles / server.cpu_rate

    def queue_latency(self, server):
        return server.queue_time

    def total_latency(self, task, server):
        tx = self.transmission_latency(task, server)
        queue = self.queue_latency(server)
        processing = self.processing_latency(task, server)

        return tx + queue + processing

    def is_feasible(self, task, server):
        latency = self.total_latency(task, server)

        deadline_ok = (
            task.arrival_time + latency <= task.deadline
        )

        memory_ok = (
            server.available_memory >= task.memory
        )

        return deadline_ok and memory_ok

    def get_action_mask(self):
        if self.current_task is None:
            raise ValueError("No task has been assigned.")

        mask = [
            int(self.is_feasible(self.current_task, server))
            for server in self.servers
        ]

        return np.array(mask, dtype=np.int8)

    def execute(self, server_id):

        if self.current_task is None:
            raise ValueError("No task has been assigned.")

        task = self.current_task
        server = self.servers[server_id]

        latency = self.total_latency(task, server)

        success = (
            task.arrival_time + latency <= task.deadline
        )

        if success:
            server.queue_time += self.processing_latency(
                task, server
            )

            server.memory_used += task.memory

            reward = 10.0 - latency

        else:
            reward = -10.0

        return {
            "success": success,
            "latency": latency,
            "reward": reward,
            "server_id": server_id,
        }

    def get_state(self):

        if self.current_task is None:
            return None

        state = []

        task = self.current_task

        state.extend([
            task.cpu_cycles,
            task.memory,
            task.payload,
            task.deadline_slack,
        ])

        for server in self.servers:
            state.extend([
                server.cpu_rate,
                server.available_memory,
                server.bandwidth,
                server.queue_time,
            ])

        return np.array(state, dtype=np.float32)