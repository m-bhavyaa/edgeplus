from env.edge_env import EdgePlusEnv
from env.server import Server
from env.task import Task


servers = [
    Server(
        id=0,
        cluster=0,
        cpu_rate=1e9,
        memory_capacity=4096,
        bandwidth=10e6
    ),

    Server(
        id=1,
        cluster=0,
        cpu_rate=2e9,
        memory_capacity=8192,
        bandwidth=20e6
    )
]


env = EdgePlusEnv(servers)

env.reset()


task1 = Task(
    id=1,
    arrival_time=0.0,
    deadline=10.0,
    cluster=0,
    service_class="URLLC",
    cpu_cycles=4e9,
    memory=1000,
    payload=1e6
)


task2 = Task(
    id=2,
    arrival_time=1.0,
    deadline=10.0,
    cluster=0,
    service_class="URLLC",
    cpu_cycles=2e9,
    memory=1000,
    payload=1e6
)


print("========== TASK 1 ==========")

env.set_task(task1)

print("Simulation time:", env.time)

result1 = env.execute(0)

print(result1)

print("\nServer 0 jobs:")
print(servers[0].active_jobs)

print(
    "Server 0 available memory:",
    servers[0].available_memory
)


print("\n========== TASK 2 ==========")

env.set_task(task2)

print("Simulation time:", env.time)

print(
    "Server 0 queue:",
    servers[0].queue_latency
    if hasattr(servers[0], "queue_latency")
    else servers[0].last_finish_time() - env.time
)

print(
    "Server 0 available memory:",
    servers[0].available_memory
)


result2 = env.execute(0)

print(result2)


print("\nServer 0 jobs:")
print(servers[0].active_jobs)


print("\n========== ADVANCE TIME ==========")

env.advance_time(5.0)

print("Simulation time:", env.time)

print(
    "Server 0 jobs after cleanup:"
)

print(servers[0].active_jobs)

print(
    "Server 0 available memory:",
    servers[0].available_memory
)