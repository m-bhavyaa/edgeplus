"""Load the JSON experiment configuration and apply dotted-key overrides.

Example:
    cfg = load_config(overrides={"consensus.mode": "mask_aware",
                                 "workload.regime": "stress"})
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "configs" / "base.json"


def set_dotted(cfg: dict, key: str, value) -> None:
    """Set cfg['a']['b'] = value for key 'a.b'. Raises KeyError on typos."""
    parts = key.split(".")
    node = cfg
    for p in parts[:-1]:
        node = node[p]
    if parts[-1] not in node:
        raise KeyError(f"unknown config key: {key}")
    node[parts[-1]] = value


def load_config(path: str | Path | None = None, overrides: dict | None = None) -> dict:
    cfg = json.loads(Path(path or DEFAULT_CONFIG).read_text())
    cfg = copy.deepcopy(cfg)
    for k, v in (overrides or {}).items():
        set_dotted(cfg, k, v)
    return cfg
