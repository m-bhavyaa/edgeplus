from dataclasses import dataclass, field


@dataclass
class Server:

    id: int
    cluster: int
    cpu_rate: float
    memory_capacity: float
    bandwidth: float
    channel_gain: float = 1.0

    energy_budget: float = 1000.0
    energy_used: float = 0.0

    supported_slices: tuple = (
        "URLLC",
        "eMBB",
        "mMTC"
    )

    slice_capacity: dict = field(
        default_factory=lambda: {
            "URLLC": 10,
            "eMBB": 10,
            "mMTC": 10
        }
    )

    active_jobs: list = field(
        default_factory=list
    )

    @property
    def available_memory(self):

        used = sum(
            job["memory"]
            for job in self.active_jobs
        )

        return (
            self.memory_capacity
            - used
        )

    @property
    def available_energy(self):

        return (
            self.energy_budget
            - self.energy_used
        )

    @property
    def queue_time(self):

        return max(
            0.0,
            self.last_finish_time()
        )

    def last_finish_time(self):

        if not self.active_jobs:
            return 0.0

        return max(
            job["finish_time"]
            for job in self.active_jobs
        )

    def release_completed_jobs(
        self,
        current_time
    ):

        self.active_jobs = [
            job
            for job in self.active_jobs
            if job["finish_time"] > current_time
        ]

    def active_slice_count(
        self,
        service_class
    ):

        return sum(
            1
            for job in self.active_jobs
            if job["service_class"]
            == service_class
        )

    def add_job(
        self,
        task_id,
        service_class,
        memory,
        start_time,
        finish_time
    ):

        self.active_jobs.append(
            {
                "task_id": task_id,
                "service_class": service_class,
                "memory": memory,
                "start_time": start_time,
                "finish_time": finish_time
            }
        )