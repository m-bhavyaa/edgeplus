from dataclasses import dataclass, field


@dataclass
class Server:

    id: int
    cluster: int
    cpu_rate: float
    memory_capacity: float
    bandwidth: float

    energy_budget: float = 1000.0
    energy_used: float = 0.0

    active_jobs: list = field(default_factory=list)

    @property
    def available_memory(self):

        used = sum(
            job["memory"]
            for job in self.active_jobs
        )

        return self.memory_capacity - used

    @property
    def queue_time(self):

        if not self.active_jobs:
            return 0.0

        latest_finish = max(
            job["finish_time"]
            for job in self.active_jobs
        )

        return max(
            0.0,
            latest_finish
        )

    @property
    def available_energy(self):

        return (
            self.energy_budget
            - self.energy_used
        )

    def release_completed_jobs(self, current_time):

        self.active_jobs = [
            job
            for job in self.active_jobs
            if job["finish_time"] > current_time
        ]

    def last_finish_time(self):

        if not self.active_jobs:
            return 0.0

        return max(
            job["finish_time"]
            for job in self.active_jobs
        )

    def add_job(
        self,
        task_id,
        memory,
        start_time,
        finish_time
    ):

        self.active_jobs.append(
            {
                "task_id": task_id,
                "memory": memory,
                "start_time": start_time,
                "finish_time": finish_time
            }
        )