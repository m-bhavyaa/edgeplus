"""Shared fixtures. Adds the repo root to sys.path so tests run from any cwd."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.config import load_config  # noqa: E402
from env.edge_env import EdgePlusEnv  # noqa: E402
from env.task import Task  # noqa: E402

# Server ids under configs/base.json: cluster c has stationary 3c (1 GHz),
# 3c+1 (2 GHz), mobile 3c+2; cloud is id 30. Degraded servers: 3 and 12.
FAST_LOCAL_4 = 13
SLOW_LOCAL_4 = 12
MOBILE_4 = 14
CLOUD = 30


def make_task(**kw):
    base = dict(id=1, arrival_time=0.0, deadline=10.0, cluster=4, service_class="URLLC",
                cpu_cycles=2e9, memory=500, payload=1e6, priority=3.0)
    base.update(kw)
    return Task(**base)


@pytest.fixture
def cfg():
    # Deterministic executor for exact-value tests.
    return load_config(overrides={"simulator.service_noise_cv": 0.0,
                                  "servers.degraded_servers": []})


@pytest.fixture
def env(cfg):
    return EdgePlusEnv(cfg, seed=0)
