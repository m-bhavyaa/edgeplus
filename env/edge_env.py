import numpy as np

from .task import Task
from .server import Server
from .topology import Topology


'''class EdgePlusEnv:

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

class EdgePlusEnv:

    def __init__(self, servers):

        self.servers = servers
        self.topology = Topology()

        self.current_task = None
        self.time = 0.0

    # --------------------------------------------------
    # RESET
    # --------------------------------------------------

    def reset(self):

        self.time = 0.0
        self.current_task = None

        for server in self.servers:

            server.active_jobs.clear()
            server.energy_used = 0.0

        return self.get_state()

    # --------------------------------------------------
    # TIME
    # --------------------------------------------------

    def advance_time(self, new_time):

        if new_time < self.time:

            raise ValueError(
                "Simulation time cannot move backwards."
            )

        self.time = new_time

        for server in self.servers:

            server.release_completed_jobs(
                self.time
            )

    # --------------------------------------------------
    # TASK
    # --------------------------------------------------

    def set_task(self, task):

        self.advance_time(
            task.arrival_time
        )

        self.current_task = task

    # --------------------------------------------------
    # TOPOLOGY
    # --------------------------------------------------

    def candidate_servers(self, task):

        local_servers = [
            server
            for server in self.servers
            if server.cluster == task.cluster
        ]

        neighbor_clusters = (
            self.topology.get_neighbors(
                task.cluster
            )
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

    def transmission_latency(
        self,
        task,
        server
    ):

        rate = max(
            server.bandwidth,
            1e-9
        )

        return task.payload / rate

    def movement_latency(
        self,
        task,
        server
    ):

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

    def processing_latency(
        self,
        task,
        server
    ):

        return (
            task.cpu_cycles
            / server.cpu_rate
        )

    def queue_latency(
        self,
        server
    ):

        last_finish = (
            server.last_finish_time()
        )

        return max(
            0.0,
            last_finish - self.time
        )

    def total_latency(
        self,
        task,
        server
    ):

        transmission = (
            self.transmission_latency(
                task,
                server
            )
        )

        movement = (
            self.movement_latency(
                task,
                server
            )
        )

        queue = (
            self.queue_latency(
                server
            )
        )

        processing = (
            self.processing_latency(
                task,
                server
            )
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

    def is_feasible(
        self,
        task,
        server
    ):

        if server not in self.candidate_servers(
            task
        ):

            return False

        latency = self.total_latency(
            task,
            server
        )

        deadline_ok = (
            task.arrival_time
            + latency
            <= task.deadline
        )

        memory_ok = (
            server.available_memory
            >= task.memory
        )

        return (
            deadline_ok
            and memory_ok
        )

    def get_action_mask(self):

        if self.current_task is None:

            raise ValueError(
                "No task has been assigned."
            )

        mask = [
            int(
                self.is_feasible(
                    self.current_task,
                    server
                )
            )
            for server in self.servers
        ]

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

        if not self.is_feasible(
            task,
            server
        ):

            return {
                "success": False,
                "latency": None,
                "queue": None,
                "processing": None,
                "reward": -10.0,
                "server_id": server_id
            }

        queue = self.queue_latency(
            server
        )

        processing = (
            self.processing_latency(
                task,
                server
            )
        )

        transmission = (
            self.transmission_latency(
                task,
                server
            )
        )

        movement = (
            self.movement_latency(
                task,
                server
            )
        )

        latency = (
            transmission
            + movement
            + queue
            + processing
        )

        start_time = (
            self.time
            + queue
        )

        finish_time = (
            start_time
            + processing
        )

        server.add_job(
            task_id=task.id,
            memory=task.memory,
            start_time=start_time,
            finish_time=finish_time
        )

        reward = (
            10.0
            - latency
        )

        return {
            "success": True,
            "latency": latency,
            "queue": queue,
            "processing": processing,
            "transmission": transmission,
            "movement": movement,
            "start_time": start_time,
            "finish_time": finish_time,
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

            task.deadline
            - self.time,

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



class EdgePlusEnv:

    def __init__(self, servers):

        self.servers = servers
        self.topology = Topology()

        self.current_task = None
        self.time = 0.0

    # ==================================================
    # RESET
    # ==================================================

    def reset(self):

        self.time = 0.0
        self.current_task = None

        for server in self.servers:

            server.active_jobs.clear()
            server.energy_used = 0.0

        return self.get_state()

    # ==================================================
    # TIME
    # ==================================================

    def advance_time(self, new_time):

        if new_time < self.time:

            raise ValueError(
                "Simulation time cannot move backwards."
            )

        self.time = new_time

        for server in self.servers:

            server.release_completed_jobs(
                self.time
            )

    # ==================================================
    # TASK
    # ==================================================

    def set_task(self, task):

        self.advance_time(
            task.arrival_time
        )

        self.current_task = task

    # ==================================================
    # TOPOLOGY
    # ==================================================

    def candidate_servers(self, task):

        local_servers = [
            server
            for server in self.servers
            if server.cluster == task.cluster
        ]

        neighbor_clusters = (
            self.topology.get_neighbors(
                task.cluster
            )
        )

        neighbor_servers = [
            server
            for server in self.servers
            if server.cluster in neighbor_clusters
        ]

        return local_servers + neighbor_servers

    # ==================================================
    # COMMUNICATION MODEL
    # ==================================================

    def effective_rate(
        self,
        task,
        server
    ):

        base_rate = server.bandwidth

        channel_factor = max(
            server.channel_gain,
            1e-9
        )

        return base_rate * channel_factor

    def transmission_latency(
        self,
        task,
        server
    ):

        rate = self.effective_rate(
            task,
            server
        )

        return (
            task.payload
            / rate
        )

    # ==================================================
    # MOVEMENT MODEL
    # ==================================================

    def movement_latency(
        self,
        task,
        server
    ):

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

    # ==================================================
    # QUEUE MODEL
    # ==================================================

    def queue_latency(
        self,
        server
    ):

        last_finish = (
            server.last_finish_time()
        )

        return max(
            0.0,
            last_finish - self.time
        )

    # ==================================================
    # PROCESSING MODEL
    # ==================================================

    def processing_latency(
        self,
        task,
        server
    ):

        return (
            task.cpu_cycles
            / server.cpu_rate
        )

    # ==================================================
    # TOTAL LATENCY
    # ==================================================

    def latency_components(
        self,
        task,
        server
    ):

        return {
            "transmission": (
                self.transmission_latency(
                    task,
                    server
                )
            ),
            "movement": (
                self.movement_latency(
                    task,
                    server
                )
            ),
            "queue": (
                self.queue_latency(
                    server
                )
            ),
            "processing": (
                self.processing_latency(
                    task,
                    server
                )
            )
        }

    def total_latency(
        self,
        task,
        server
    ):

        components = self.latency_components(
            task,
            server
        )

        return sum(
            components.values()
        )

    # ==================================================
    # FEASIBILITY
    # ==================================================

    def is_feasible(
        self,
        task,
        server
    ):

        if server not in self.candidate_servers(
            task
        ):

            return False

        latency = self.total_latency(
            task,
            server
        )

        deadline_ok = (
            task.arrival_time
            + latency
            <= task.deadline
        )

        memory_ok = (
            server.available_memory
            >= task.memory
        )

        return (
            deadline_ok
            and memory_ok
        )

    def get_action_mask(self):

        if self.current_task is None:

            raise ValueError(
                "No task has been assigned."
            )

        return np.array(
            [
                int(
                    self.is_feasible(
                        self.current_task,
                        server
                    )
                )
                for server in self.servers
            ],
            dtype=np.int8
        )

    # ==================================================
    # EXECUTION
    # ==================================================

    def execute(self, server_id):

        if self.current_task is None:

            raise ValueError(
                "No task has been assigned."
            )

        task = self.current_task
        server = self.servers[server_id]

        if not self.is_feasible(
            task,
            server
        ):

            return {
                "success": False,
                "latency": None,
                "reward": -10.0,
                "server_id": server_id
            }

        components = self.latency_components(
            task,
            server
        )

        latency = sum(
            components.values()
        )

        start_time = (
            self.time
            + components["queue"]
        )

        finish_time = (
            start_time
            + components["processing"]
        )

        server.add_job(
            task_id=task.id,
            memory=task.memory,
            start_time=start_time,
            finish_time=finish_time
        )

        reward = 10.0 - latency

        return {
            "success": True,
            "latency": latency,
            "transmission": components["transmission"],
            "movement": components["movement"],
            "queue": components["queue"],
            "processing": components["processing"],
            "start_time": start_time,
            "finish_time": finish_time,
            "reward": reward,
            "server_id": server_id
        }

    # ==================================================
    # STATE
    # ==================================================

    def get_state(self):

        if self.current_task is None:

            return None

        task = self.current_task

        state = [

            task.cpu_cycles,

            task.memory,

            task.payload,

            task.deadline - self.time,

            task.cluster
        ]

        for server in self.servers:

            state.extend([

                server.cpu_rate,

                server.available_memory,

                server.bandwidth,

                server.channel_gain,

                server.queue_time
                if hasattr(server, "queue_time")
                else self.queue_latency(server)
            ])

        return np.array(
            state,
            dtype=np.float32
        )'''


class EdgePlusEnv:

    def __init__(
        self,
        servers,
        slice_quotas=None
    ):

        self.servers = servers
        self.topology = Topology()

        self.current_task = None
        self.time = 0.0

        if slice_quotas is None:

            self.slice_quotas = {
                "URLLC": 10,
                "eMBB": 10,
                "mMTC": 10
            }

        else:

            self.slice_quotas = slice_quotas

    # ==================================================
    # RESET
    # ==================================================

    def reset(self):

        self.time = 0.0
        self.current_task = None

        for server in self.servers:

            server.active_jobs.clear()
            server.energy_used = 0.0

        return self.get_state()

    # ==================================================
    # TIME
    # ==================================================

    def advance_time(self, new_time):

        if new_time < self.time:

            raise ValueError(
                "Simulation time cannot move backwards."
            )

        self.time = new_time

        for server in self.servers:

            server.release_completed_jobs(
                self.time
            )

    # ==================================================
    # TASK
    # ==================================================

    def set_task(self, task):

        self.advance_time(
            task.arrival_time
        )

        self.current_task = task

    # ==================================================
    # TOPOLOGY / ROUTING
    # ==================================================

    def routing_region(
        self,
        task,
        server
    ):

        if server.cluster == task.cluster:

            return 0

        if self.topology.are_neighbors(
            task.cluster,
            server.cluster
        ):

            return 1

        return 2

    def candidate_servers(self, task):

        return [
            server
            for server in self.servers
            if self.routing_region(
                task,
                server
            ) < 2
        ]

    # ==================================================
    # COMMUNICATION
    # ==================================================

    def effective_rate(
        self,
        task,
        server
    ):

        return (
            server.bandwidth
            * max(
                server.channel_gain,
                1e-9
            )
        )

    def transmission_latency(
        self,
        task,
        server
    ):

        return (
            task.payload
            / self.effective_rate(
                task,
                server
            )
        )

    # ==================================================
    # MOVEMENT
    # ==================================================

    def movement_latency(
        self,
        task,
        server
    ):

        if server.cluster == task.cluster:

            return 0.0

        if self.topology.are_neighbors(
            task.cluster,
            server.cluster
        ):

            distance = (
                self.topology.distance(
                    task.cluster,
                    server.cluster
                )
            )

            return 0.01 * distance

        return 0.0

    # ==================================================
    # QUEUE
    # ==================================================

    def queue_latency(
        self,
        server
    ):

        return max(
            0.0,
            server.last_finish_time()
            - self.time
        )

    # ==================================================
    # PROCESSING
    # ==================================================

    def processing_latency(
        self,
        task,
        server
    ):

        return (
            task.cpu_cycles
            / server.cpu_rate
        )

    # ==================================================
    # LATENCY
    # ==================================================

    def latency_components(
        self,
        task,
        server
    ):

        return {
            "transmission": (
                self.transmission_latency(
                    task,
                    server
                )
            ),

            "movement": (
                self.movement_latency(
                    task,
                    server
                )
            ),

            "queue": (
                self.queue_latency(
                    server
                )
            ),

            "processing": (
                self.processing_latency(
                    task,
                    server
                )
            )
        }

    def total_latency(
        self,
        task,
        server
    ):

        components = (
            self.latency_components(
                task,
                server
            )
        )

        return sum(
            components.values()
        )

    # ==================================================
    # RESOURCE CHECKS
    # ==================================================

    def memory_feasible(
        self,
        task,
        server
    ):

        return (
            server.available_memory
            >= task.memory
        )

    def energy_required(
        self,
        task,
        server
    ):

        processing = (
            self.processing_latency(
                task,
                server
            )
        )

        return (
            processing
            * 1.0
        )

    def energy_feasible(
        self,
        task,
        server
    ):

        required = (
            self.energy_required(
                task,
                server
            )
        )

        return (
            server.available_energy
            >= required
        )

    # ==================================================
    # SLICE CHECK
    # ==================================================

    def slice_feasible(
        self,
        task,
        server
    ):

        service_class = (
            task.service_class
        )

        if service_class not in (
            server.supported_slices
        ):

            return False

        active = (
            server.active_slice_count(
                service_class
            )
        )

        capacity = (
            server.slice_capacity.get(
                service_class,
                0
            )
        )

        global_quota = (
            self.slice_quotas.get(
                service_class,
                0
            )
        )

        return (
            active < capacity
            and active < global_quota
        )

    # ==================================================
    # DEADLINE CHECK
    # ==================================================

    def deadline_feasible(
        self,
        task,
        server
    ):

        latency = (
            self.total_latency(
                task,
                server
            )
        )

        completion_time = (
            task.arrival_time
            + latency
        )

        return (
            completion_time
            <= task.deadline
        )

    # ==================================================
    # ROUTING CHECK
    # ==================================================

    def routing_feasible(
        self,
        task,
        server
    ):

        region = (
            self.routing_region(
                task,
                server
            )
        )

        return region in (0, 1)

    # ==================================================
    # COMPLETE FEASIBILITY
    # ==================================================

    def feasibility_reasons(
        self,
        task,
        server
    ):

        reasons = {}

        reasons["routing"] = (
            self.routing_feasible(
                task,
                server
            )
        )

        reasons["slice"] = (
            self.slice_feasible(
                task,
                server
            )
        )

        reasons["memory"] = (
            self.memory_feasible(
                task,
                server
            )
        )

        reasons["energy"] = (
            self.energy_feasible(
                task,
                server
            )
        )

        reasons["deadline"] = (
            self.deadline_feasible(
                task,
                server
            )
        )

        reasons["feasible"] = all(
            reasons.values()
        )

        return reasons

    def is_feasible(
        self,
        task,
        server
    ):

        reasons = (
            self.feasibility_reasons(
                task,
                server
            )
        )

        return reasons["feasible"]

    # ==================================================
    # ACTION MASK
    # ==================================================

    def get_action_mask(self):

        if self.current_task is None:

            raise ValueError(
                "No task has been assigned."
            )

        return np.array(
            [
                int(
                    self.is_feasible(
                        self.current_task,
                        server
                    )
                )
                for server in self.servers
            ],
            dtype=np.int8
        )

    # ==================================================
    # EXECUTION
    # ==================================================

    def execute(
        self,
        server_id
    ):

        if self.current_task is None:

            raise ValueError(
                "No task has been assigned."
            )

        task = self.current_task
        server = self.servers[server_id]

        if not self.is_feasible(
            task,
            server
        ):

            return {
                "success": False,
                "latency": None,
                "reward": -10.0,
                "server_id": server_id
            }

        components = (
            self.latency_components(
                task,
                server
            )
        )

        latency = sum(
            components.values()
        )

        start_time = (
            self.time
            + components["queue"]
        )

        finish_time = (
            start_time
            + components["processing"]
        )

        energy = (
            self.energy_required(
                task,
                server
            )
        )

        server.energy_used += energy

        server.add_job(
            task_id=task.id,
            service_class=task.service_class,
            memory=task.memory,
            start_time=start_time,
            finish_time=finish_time
        )

        reward = (
            10.0
            - latency
        )

        return {
            "success": True,
            "latency": latency,
            "transmission": components["transmission"],
            "movement": components["movement"],
            "queue": components["queue"],
            "processing": components["processing"],
            "energy": energy,
            "start_time": start_time,
            "finish_time": finish_time,
            "reward": reward,
            "server_id": server_id
        }

    # ==================================================
    # STATE
    # ==================================================

    def get_state(self):

        if self.current_task is None:

            return None

        task = self.current_task

        state = [

            task.cpu_cycles,

            task.memory,

            task.payload,

            task.deadline - self.time,

            task.cluster
        ]

        for server in self.servers:

            state.extend([

                server.cpu_rate,

                server.available_memory,

                server.bandwidth,

                server.channel_gain,

                server.queue_time,

                server.available_energy
            ])

        return np.array(
            state,
            dtype=np.float32
        )