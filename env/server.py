"""Server model (M3). A server is stationary, mobile, or cloud (paper Sec. III-A)."""

from __future__ import annotations

from dataclasses import dataclass, field

STATIONARY, MOBILE, CLOUD = "stationary", "mobile", "cloud"
CLOUD_CLUSTER = -1  # the paper uses c(s)=0 for cloud; our edge clusters are 0..9


@dataclass
class Server:
    id: int
    cluster: int
    cpu_rate: float          # cycles / s
    memory_capacity: float   # MB
    bandwidth: float         # bit / s
    channel_gain: float = 1.0
    kind: str = STATIONARY
    speed_mps: float = 0.0   # mobiles only
    energy_budget: float = float("inf")  # J; finite for mobiles only (Eq. 3)
    slowdown: float = 1.0    # >1 for "degraded" servers (drives reputation)
    energy_used: float = 0.0
    active_jobs: list = field(default_factory=list)

    @property
    def available_memory(self) -> float:
        return self.memory_capacity - sum(j["memory"] for j in self.active_jobs)

    @property
    def available_energy(self) -> float:
        return self.energy_budget - self.energy_used

    def last_finish_time(self) -> float:
        return max((j["finish_time"] for j in self.active_jobs), default=0.0)

    def backlog(self, now: float) -> float:
        """Seconds until this server is idle (relative, fixes audit D2)."""
        return max(0.0, self.last_finish_time() - now)

    def release_completed_jobs(self, now: float) -> None:
        self.active_jobs = [j for j in self.active_jobs if j["finish_time"] > now]

    def add_job(self, task_id, service_class, memory, start_time, finish_time) -> None:
        self.active_jobs.append({"task_id": task_id, "service_class": service_class,
                                 "memory": memory, "start_time": start_time,
                                 "finish_time": finish_time})


def build_servers(server_cfg: dict, num_clusters: int) -> list[Server]:
    """Per cluster: the configured stationary servers, then mobiles; one cloud last."""
    servers: list[Server] = []
    degraded = set(server_cfg.get("degraded_servers", []))
    for c in range(num_clusters):
        for spec in server_cfg["stationary"]:
            servers.append(Server(id=len(servers), cluster=c, cpu_rate=spec["cpu_rate"],
                                  memory_capacity=spec["memory"], bandwidth=spec["bandwidth"],
                                  channel_gain=spec["channel_gain"]))
        m = server_cfg["mobile"]
        for _ in range(server_cfg["mobile_per_cluster"]):
            servers.append(Server(id=len(servers), cluster=c, cpu_rate=m["cpu_rate"],
                                  memory_capacity=m["memory"], bandwidth=m["bandwidth"],
                                  channel_gain=m["channel_gain"], kind=MOBILE,
                                  speed_mps=m["speed_mps"], energy_budget=m["energy_budget_j"]))
    cl = server_cfg["cloud"]
    if cl["enabled"]:
        servers.append(Server(id=len(servers), cluster=CLOUD_CLUSTER, cpu_rate=cl["cpu_rate"],
                              memory_capacity=cl["memory"], bandwidth=cl["bandwidth"],
                              channel_gain=cl["channel_gain"], kind=CLOUD))
    for s in servers:
        if s.id in degraded:
            s.slowdown = server_cfg["degraded_slowdown"]
    return servers
