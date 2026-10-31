"""Train SB3 PPO (M7, unmasked) or MaskablePPO (M8) on the baseline simulator."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from env.config import REPO_ROOT, load_config
from env.ppo_env import PPOEdgeEnv
from experiments.presets import BASELINE


def train(masked: bool, timesteps: int, regime: str, out: Path) -> Path:
    cfg = load_config(overrides={**BASELINE, "workload.regime": regime})
    env = PPOEdgeEnv(cfg, num_tasks=cfg["train_tasks_per_episode"], seed=cfg["seeds"]["train_base"])
    p = cfg["ppo"]
    kwargs = dict(learning_rate=p["lr"], n_steps=p["n_steps"], batch_size=p["batch_size"],
                  n_epochs=p["n_epochs"], gamma=p["gamma"], gae_lambda=p["gae_lambda"],
                  clip_range=p["clip_range"], ent_coef=p["ent_coef"], verbose=0,
                  device="cpu", seed=cfg["seeds"]["train_base"])
    if masked:
        from sb3_contrib import MaskablePPO
        model = MaskablePPO("MlpPolicy", env, **kwargs)
    else:
        from stable_baselines3 import PPO
        model = PPO("MlpPolicy", env, **kwargs)
    t0 = time.time()
    model.learn(total_timesteps=timesteps)
    out.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(out))
    meta = {"algo": "MaskablePPO" if masked else "PPO", "timesteps": timesteps, "regime": regime,
            "train_seed_base": cfg["seeds"]["train_base"], "train_seconds": time.time() - t0,
            "episodes_seen": env.episode, "ppo": p}
    Path(str(out) + ".json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return out


def main(masked: bool, default_name: str) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timesteps", type=int, default=60000)
    ap.add_argument("--smoke", action="store_true", help="2048 steps, for checking the pipeline")
    ap.add_argument("--regime", default="medium")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "models" / default_name)
    a = ap.parse_args()
    train(masked, 2048 if a.smoke else a.timesteps, a.regime, a.out)
