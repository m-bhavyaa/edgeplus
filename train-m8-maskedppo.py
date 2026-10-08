from sb3_contrib import MaskablePPO
from env.ppo_env import PPOEdgeEnv


env = PPOEdgeEnv(
    num_tasks=500,
    seed=42
)

model = MaskablePPO(
    "MlpPolicy",
    env,
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
    total_timesteps=50000
)

model.save(
    "models/m8_masked_ppo"
)