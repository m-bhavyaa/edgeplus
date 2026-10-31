"""Shared fixtures. Adds the repo root to sys.path so tests run from any cwd."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.edge_env import EdgePlusEnv  # noqa: E402
from env.server import Server  # noqa: E402
from env.task import Task  # noqa: E402


def make_servers():
    """The 20-server inventory used by ppo_env.py / experiment-m6.py."""
    servers = []
    for c in range(10):
        servers.append(Server(id=2 * c, cluster=c, cpu_rate=1e9, memory_capacity=4096,
                              bandwidth=10e6, channel_gain=0.8))
        servers.append(Server(id=2 * c + 1, cluster=c, cpu_rate=2e9, memory_capacity=8192,
                              bandwidth=20e6, channel_gain=1.2))
    return servers


def make_task(**kw):
    base = dict(id=1, arrival_time=0.0, deadline=10.0, cluster=4, service_class="URLLC",
                cpu_cycles=2e9, memory=500, payload=1e6, priority=3.0)
    base.update(kw)
    return Task(**base)


@pytest.fixture
def env():
    e = EdgePlusEnv(servers=make_servers(),
                    slice_quotas={"URLLC": 10, "eMBB": 10, "mMTC": 10})
    e.reset()
    return e
