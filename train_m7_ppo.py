"""M7: train unmasked PPO.  python train_m7_ppo.py [--smoke] [--timesteps N]"""
from agents.sb3_train import main

if __name__ == "__main__":
    main(masked=False, default_name="m7_ppo")
