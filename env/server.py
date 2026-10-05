from dataclasses import dataclass


@dataclass
class Server:
    id: int
    cluster: int
    cpu_rate: float
    memory_capacity: float
    bandwidth: float
    queue_time: float = 0.0
    memory_used: float = 0.0
    energy_budget: float = 1000.0
    energy_used: float = 0.0

    @property
    def available_memory(self):
        return self.memory_capacity - self.memory_used

    @property
    def available_energy(self):
        return self.energy_budget - self.energy_used