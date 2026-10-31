"""M8: train MaskablePPO.  python train_m8_masked_ppo.py [--smoke] [--timesteps N]"""
from agents.sb3_train import main

if __name__ == "__main__":
    main(masked=True, default_name="m8_masked_ppo")
