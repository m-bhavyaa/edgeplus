import numpy as np

from sb3_contrib import MaskablePPO
from env.ppo_env import PPOEdgeEnv


def evaluate():

    env = PPOEdgeEnv(
        num_tasks=1000,
        seed=100
    )

    model = MaskablePPO.load(
        "models/m8_masked_ppo",
        env=env
    )

    obs, _ = env.reset()

    total_tasks = 0
    successful_tasks = 0
    total_reward = 0.0
    total_energy = 0.0
    total_feasible_actions = 0
    tasks_with_no_feasible_action = 0
    latencies = []
    feasible_tasks = 0
    successful_feasible_tasks = 0

    while True:

        action_masks = env.action_masks()

        num_feasible = action_masks.sum()

        total_feasible_actions += num_feasible
        if num_feasible>0:
            feasible_tasks+=1

        if num_feasible == 0:
            tasks_with_no_feasible_action += 1

        action, _ = model.predict(
            obs,
            action_masks=action_masks,
            deterministic=True
        )

        (
            obs,
            reward,
            terminated,
            truncated,
            info
        ) = env.step(action)
        if info["success"] and num_feasible > 0:
            successful_feasible_tasks += 1
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
        "\n========== M8 Masked PPO =========="
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
    print(
        f"Average feasible actions: "
        f"{total_feasible_actions / total_tasks:.2f}"
    )

    print(
        f"Tasks with no feasible action: "
        f"{tasks_with_no_feasible_action}"
    )
    
    print(
        f"Tasks with >=1 feasible action: "
        f"{feasible_tasks}"
    )

    print(
        f"Success among feasible tasks: "
        f"{successful_feasible_tasks / feasible_tasks * 100:.2f}%"
        if feasible_tasks
        else "Success among feasible tasks: 0.00%"
    )

if __name__ == "__main__":
    evaluate()