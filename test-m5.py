from env.edge_env import EdgePlusEnv
from env.server import Server
from env.task import Task


servers = []

server_id = 0

for cluster_id in range(10):

    servers.append(
        Server(
            id=server_id,
            cluster=cluster_id,
            cpu_rate=1e9,
            memory_capacity=4096,
            bandwidth=10e6,
            channel_gain=0.8
        )
    )

    server_id += 1

    servers.append(
        Server(
            id=server_id,
            cluster=cluster_id,
            cpu_rate=2e9,
            memory_capacity=8192,
            bandwidth=20e6,
            channel_gain=1.2
        )
    )

    server_id += 1


env = EdgePlusEnv(
    servers=servers,
    slice_quotas={
        "URLLC": 10,
        "eMBB": 10,
        "mMTC": 10
    }
)

env.reset()


task = Task(
    id=1,
    arrival_time=0.0,
    deadline=10.0,
    cluster=4,
    service_class="URLLC",
    cpu_cycles=2e9,
    memory=500,
    payload=1e6,
    priority=3.0
)

env.set_task(task)


print("========== TASK ==========")

print(
    "Task:",
    task.id
)

print(
    "Cluster:",
    task.cluster
)

print(
    "Service class:",
    task.service_class
)

print(
    "Deadline:",
    task.deadline
)


print("\n========== SERVER CHECKS ==========")

for server in servers:

    reasons = env.feasibility_reasons(
        task,
        server
    )

    print(
        f"\nServer {server.id} "
        f"(cluster {server.cluster})"
    )

    print(
        "Routing:",
        reasons["routing"]
    )

    print(
        "Slice:",
        reasons["slice"]
    )

    print(
        "Memory:",
        reasons["memory"]
    )

    print(
        "Energy:",
        reasons["energy"]
    )

    print(
        "Deadline:",
        reasons["deadline"]
    )

    print(
        "FEASIBLE:",
        reasons["feasible"]
    )


print("\n========== ACTION MASK ==========")

print(
    env.get_action_mask()
)