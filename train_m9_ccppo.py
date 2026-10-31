"""M9: train CCPPO.

    python train_m9_ccppo.py                       # masks + advisory + ledger (EdgePlus inner loop)
    python train_m9_ccppo.py --no-advisory --no-ledger --out models/m9_ccppo_plain.pt
    python train_m9_ccppo.py --smoke               # 2k steps, pipeline check only
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from agents.ccppo import CCPPO
from env.config import REPO_ROOT, load_config


def train(out: Path, timesteps: int, masks=True, advisory=True, ledger=True, regime="medium"):
    cfg = load_config(overrides={"workload.regime": regime, "ledger.enabled": ledger,
                                 "advisory.enabled": advisory, "consensus.mode": "off"})
    pol = CCPPO(cfg, use_masks=masks, use_advisory=advisory, seed=cfg["seeds"]["train_base"])
    t0 = time.time()
    log = pol.train(timesteps, log_path=Path(str(out) + ".log.json"))
    pol.save(out)
    meta = {"timesteps": timesteps, "masks": masks, "advisory": advisory, "ledger": ledger,
            "regime": regime, "episodes": len(log), "train_seconds": time.time() - t0,
            "last_episode_success": log[-1]["success"] if log else None, "ccppo": cfg["ccppo"]}
    Path(str(out) + ".json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return pol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timesteps", type=int, default=60000)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--no-masks", action="store_true")
    ap.add_argument("--no-advisory", action="store_true")
    ap.add_argument("--no-ledger", action="store_true")
    ap.add_argument("--regime", default="medium")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "models" / "m9_ccppo.pt")
    a = ap.parse_args()
    train(a.out, 2000 if a.smoke else a.timesteps, not a.no_masks, not a.no_advisory,
          not a.no_ledger, a.regime)


if __name__ == "__main__":
    main()
