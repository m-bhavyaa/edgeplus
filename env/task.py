from dataclasses import dataclass


@dataclass
class Task:
    id: int
    arrival_time: float
    deadline: float
    cluster: int
    service_class: str
    cpu_cycles: float
    memory: float
    payload: float
    priority: float = 1.0

    @property
    def deadline_slack(self):
        return self.deadline - self.arrival_time