from env.edge_env import EdgePlusEnv
from env.server import Server
from env.task import Task


servers = [

    Server(
        id=0,
        cluster=0,
        cpu_rate=1e9,
        memory_capacity=4096,
        bandwidth=10e6,
        channel_gain=0.8
    ),

    Server(
        id=1,
        cluster=0,
        cpu_rate=2e9,
        memory_capacity=8192,
        bandwidth=20e6,
        channel_gain=1.2
    ),

    Server(
        id=2,
        cluster=1,
        cpu_rate=1e9,
        memory_capacity=4096,
        bandwidth=5e6,
        channel_gain=0.5
    )
]


env = EdgePlusEnv(servers)

env.reset()


task = Task(
    id=1,
    arrival_time=0.0,
    deadline=10.0,
    cluster=0,
    service_class="URLLC",
    cpu_cycles=2e9,
    memory=500,
    payload=10e6
)


env.set_task(task)


print("========== TASK ==========")

print(
    "Cluster:",
    task.cluster
)

print(
    "Payload:",
    task.payload / 1e6,
    "MB"
)

print(
    "Deadline:",
    task.deadline,
    "s"
)


print("\n========== LATENCY ==========")


for server in servers:

    components = env.latency_components(
        task,
        server
    )

    total = env.total_latency(
        task,
        server
    )

    print(
        f"\nServer {server.id}"
    )

    print(
        "Effective rate:",
        env.effective_rate(
            task,
            server
        ) / 1e6,
        "Mbps"
    )

    print(
        "Transmission:",
        round(
            components["transmission"],
            4
        ),
        "s"
    )

    print(
        "Movement:",
        round(
            components["movement"],
            4
        ),
        "s"
    )

    print(
        "Queue:",
        round(
            components["queue"],
            4
        ),
        "s"
    )

    print(
        "Processing:",
        round(
            components["processing"],
            4
        ),
        "s"
    )

    print(
        "TOTAL:",
        round(
            total,
            4
        ),
        "s"
    )

    print(
        "Feasible:",
        env.is_feasible(
            task,
            server
        )
    )


print("\n========== ACTION MASK ==========")

print(
    env.get_action_mask()
)