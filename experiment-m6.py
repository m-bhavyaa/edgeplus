import numpy as np

from env.edge_env import EdgePlusEnv
from env.server import Server
from env.task_generator import TaskGenerator


def create_servers():

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

    return servers


def run_experiment(
    num_tasks=1000,
    seed=42
):

    servers = create_servers()

    env = EdgePlusEnv(
        servers=servers,
        slice_quotas={
            "URLLC": 10,
            "eMBB": 10,
            "mMTC": 10
        }
    )

    generator = TaskGenerator(
        num_clusters=10,
        seed=seed
    )

    tasks = generator.generate_batch(
        num_tasks
    )

    rng = np.random.default_rng(seed)

    total_tasks = 0
    successful_tasks = 0
    failed_tasks = 0

    total_latency = 0.0
    total_reward = 0.0
    total_energy = 0.0

    no_feasible_action = 0

    selected_servers = {}

    latency_values = []

    for task in tasks:

        env.set_task(task)

        mask = env.get_action_mask()

        feasible_servers = np.flatnonzero(
            mask
        )

        total_tasks += 1

        if len(feasible_servers) == 0:

            no_feasible_action += 1
            failed_tasks += 1

            continue

        server_id = int(
            rng.choice(
                feasible_servers
            )
        )

        result = env.execute(
            server_id
        )

        if result["success"]:

            successful_tasks += 1

            latency = result["latency"]

            total_latency += latency
            total_energy += result["energy"]

            latency_values.append(
                latency
            )

        else:

            failed_tasks += 1

        total_reward += result["reward"]

        selected_servers[server_id] = (
            selected_servers.get(
                server_id,
                0
            ) + 1
        )

    success_rate = (
        successful_tasks
        / total_tasks
        * 100
    )

    violation_rate = (
        failed_tasks
        / total_tasks
        * 100
    )

    if latency_values:

        average_latency = (
            np.mean(
                latency_values
            )
        )

        p50_latency = (
            np.percentile(
                latency_values,
                50
            )
        )

        p95_latency = (
            np.percentile(
                latency_values,
                95
            )
        )

    else:

        average_latency = 0.0
        p50_latency = 0.0
        p95_latency = 0.0

    average_reward = (
        total_reward
        / total_tasks
    )

    average_energy = (
        total_energy
        / successful_tasks
        if successful_tasks > 0
        else 0.0
    )

    return {
        "tasks": total_tasks,
        "success_rate": success_rate,
        "violation_rate": violation_rate,
        "average_latency": average_latency,
        "p50_latency": p50_latency,
        "p95_latency": p95_latency,
        "average_reward": average_reward,
        "average_energy": average_energy,
        "no_feasible_action": no_feasible_action,
        "selected_servers": selected_servers
    }


if __name__ == "__main__":

    results = run_experiment(
        num_tasks=1000,
        seed=42
    )

    print(
        "\n========== M6 RANDOM POLICY =========="
    )

    print(
        f"Tasks: "
        f"{results['tasks']}"
    )

    print(
        f"Success rate: "
        f"{results['success_rate']:.2f}%"
    )

    print(
        f"Violation rate: "
        f"{results['violation_rate']:.2f}%"
    )

    print(
        f"Average latency: "
        f"{results['average_latency']:.4f}s"
    )

    print(
        f"P50 latency: "
        f"{results['p50_latency']:.4f}s"
    )

    print(
        f"P95 latency: "
        f"{results['p95_latency']:.4f}s"
    )

    print(
        f"Average reward: "
        f"{results['average_reward']:.4f}"
    )

    print(
        f"Average energy: "
        f"{results['average_energy']:.4f}"
    )

    print(
        f"No feasible action: "
        f"{results['no_feasible_action']}"
    )

    print(
        "\nServer selection:"
    )

    for server_id, count in sorted(
        results["selected_servers"].items()
    ):

        print(
            f"Server {server_id}: "
            f"{count}"
        )