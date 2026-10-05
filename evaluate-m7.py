import numpy as np

from stable_baselines3 import PPO

from env.ppo_env import PPOEdgeEnv


def evaluate():

    env = PPOEdgeEnv(
        num_tasks=1000,
        seed=100
    )

    model = PPO.load(
        "models/m7_ppo",
        env=env
    )

    obs, _ = env.reset()

    total_tasks = 0
    successful_tasks = 0
    total_reward = 0.0
    total_energy = 0.0

    latencies = []

    while True:

        action, _ = model.predict(
            obs,
            deterministic=True
        )

        (
            obs,
            reward,
            terminated,
            truncated,
            info
        ) = env.step(action)

        total_tasks += 1

        total_reward += reward

        if info["success"]:

            successful_tasks += 1

            latencies.append(
                info["latency"]
            )

            total_energy += (
                info["energy"]
            )

        if terminated or truncated:

            break

    success_rate = (
        successful_tasks
        / total_tasks
        * 100
    )

    if latencies:

        mean_latency = np.mean(
            latencies
        )

        p50_latency = np.percentile(
            latencies,
            50
        )

        p95_latency = np.percentile(
            latencies,
            95
        )

    else:

        mean_latency = 0.0
        p50_latency = 0.0
        p95_latency = 0.0

    mean_reward = (
        total_reward
        / total_tasks
    )

    mean_energy = (
        total_energy
        / successful_tasks
        if successful_tasks
        else 0.0
    )

    print(
        "\n========== M7 PPO =========="
    )

    print(
        f"Tasks: {total_tasks}"
    )

    print(
        f"Success rate: "
        f"{success_rate:.2f}%"
    )

    print(
        f"Failure rate: "
        f"{100 - success_rate:.2f}%"
    )

    print(
        f"Mean latency: "
        f"{mean_latency:.4f}s"
    )

    print(
        f"P50 latency: "
        f"{p50_latency:.4f}s"
    )

    print(
        f"P95 latency: "
        f"{p95_latency:.4f}s"
    )

    print(
        f"Mean reward: "
        f"{mean_reward:.4f}"
    )

    print(
        f"Mean energy: "
        f"{mean_energy:.4f}"
    )


if __name__ == "__main__":

    evaluate()