from stable_baselines3 import PPO

from env.ppo_env import PPOEdgeEnv


def main():

    env = PPOEdgeEnv(
        num_tasks=500,
        seed=42
    )

    model = PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=3e-4,
        n_steps=256,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        verbose=1,
        device="cpu"
    )

    model.learn(
        total_timesteps=10000
    )

    model.save(
        "models/m7_ppo"
    )

    env.close()


if __name__ == "__main__":
    main()