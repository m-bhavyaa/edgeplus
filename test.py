'''from env.edge_env import EdgePlusEnv
from env.server import Server
from env.task import Task


servers = [
    Server(
        id=0,
        cluster=0,
        cpu_rate=1e9,
        memory_capacity=4096,
        bandwidth=10e6,
    ),
    Server(
        id=1,
        cluster=0,
        cpu_rate=2e9,
        memory_capacity=8192,
        bandwidth=20e6,
    ),
    Server(
        id=2,
        cluster=1,
        cpu_rate=5e8,
        memory_capacity=2048,
        bandwidth=5e6,
    ),
]


env = EdgePlusEnv(servers)

env.reset()

task = Task(
    id=1,
    arrival_time=0.0,
    deadline=1.5,
    cluster=0,
    service_class="URLLC",
    cpu_cycles=2e9,
    memory=500,
    payload=1e6,
)

env.set_task(task)

print("STATE:")
print(env.get_state())

print("\nACTION MASK:")
print(env.get_action_mask())

for server in servers:
    latency = env.total_latency(task, server)

    print(
        f"Server {server.id}: "
        f"latency={latency:.4f}s, "
        f"feasible={env.is_feasible(task, server)}"
    )'''


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
            bandwidth=10e6
        )
    )

    server_id += 1

    servers.append(
        Server(
            id=server_id,
            cluster=cluster_id,
            cpu_rate=2e9,
            memory_capacity=8192,
            bandwidth=20e6
        )
    )

    server_id += 1


env = EdgePlusEnv(servers)

env.reset()


print("========== TOPOLOGY ==========")

for cluster_id in range(10):

    neighbors = env.topology.get_neighbors(
        cluster_id
    )

    print(
        f"Cluster {cluster_id}: "
        f"neighbors={neighbors}"
    )


print("\n========== SERVERS ==========")

for server in servers:

    print(
        f"Server {server.id}: "
        f"cluster={server.cluster}, "
        f"cpu={server.cpu_rate / 1e9:.1f} GHz"
    )


task = Task(
    id=1,
    arrival_time=0.0,
    deadline=2.0,
    cluster=4,
    service_class="URLLC",
    cpu_cycles=2e9,
    memory=500,
    payload=1e6
)

env.set_task(task)


print("\n========== TASK ==========")

print(
    f"Task cluster: {task.cluster}"
)

print(
    f"Deadline: {task.deadline}s"
)


print("\n========== CANDIDATE SERVERS ==========")

candidates = env.candidate_servers(task)

for server in candidates:

    print(
        f"Server {server.id} "
        f"(cluster {server.cluster})"
    )


print("\n========== ACTION MASK ==========")

mask = env.get_action_mask()

print(mask)


print("\n========== LATENCY ==========")

for server in servers:

    latency = env.total_latency(
        task,
        server
    )

    feasible = env.is_feasible(
        task,
        server
    )

    print(
        f"Server {server.id}: "
        f"cluster={server.cluster}, "
        f"latency={latency:.4f}s, "
        f"feasible={feasible}"
    )


print("\n========== EXECUTION ==========")

result = env.execute(9)

print(result)