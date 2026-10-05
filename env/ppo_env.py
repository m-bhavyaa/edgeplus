import gymnasium as gym
import numpy as np
from gymnasium import spaces

from .edge_env import EdgePlusEnv
from .server import Server
from .task_generator import TaskGenerator


class PPOEdgeEnv(gym.Env):

    def __init__(
        self,
        num_tasks=1000,
        seed=42
    ):

        super().__init__()

        self.num_tasks = num_tasks
        self.seed_value = seed

        self.rng = np.random.default_rng(seed)

        self.servers = self._create_servers()

        self.env = EdgePlusEnv(
            servers=self.servers,
            slice_quotas={
                "URLLC": 10,
                "eMBB": 10,
                "mMTC": 10
            }
        )

        self.task_generator = TaskGenerator(
            num_clusters=10,
            seed=seed
        )

        self.tasks = []
        self.task_index = 0

        observation_size = 5 + 20 * 6

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(observation_size,),
            dtype=np.float32
        )

        self.action_space = spaces.Discrete(
            20
        )

    def _create_servers(self):

        servers = []

        server_id = 0

        for cluster_id in range(10):

            servers.append(
                Server(
                    id=server_id,
                    cluster=cluster_id,
                    cpu_rate=1e9,
                    memory_capacity=4096,
                    bandwidth=10e6,
                    channel_gain=0.8
                )
            )

            server_id += 1

            servers.append(
                Server(
                    id=server_id,
                    cluster=cluster_id,
                    cpu_rate=2e9,
                    memory_capacity=8192,
                    bandwidth=20e6,
                    channel_gain=1.2
                )
            )

            server_id += 1

        return servers

    def reset(
        self,
        seed=None,
        options=None
    ):

        super().reset(
            seed=seed
        )

        if seed is not None:
            self.seed_value = seed

        self.servers = self._create_servers()

        self.env = EdgePlusEnv(
            servers=self.servers,
            slice_quotas={
                "URLLC": 10,
                "eMBB": 10,
                "mMTC": 10
            }
        )

        self.task_generator = TaskGenerator(
            num_clusters=10,
            seed=self.seed_value
        )

        self.tasks = (
            self.task_generator.generate_batch(
                self.num_tasks
            )
        )

        self.task_index = 0

        task = self.tasks[
            self.task_index
        ]

        self.env.set_task(task)

        observation = self.env.get_state()

        return observation, {}

    def step(
        self,
        action
    ):

        action = int(action)

        task = self.tasks[
            self.task_index
        ]

        result = self.env.execute(
            action
        )

        reward = result["reward"]

        success = result["success"]

        self.task_index += 1

        terminated = (
            self.task_index
            >= len(self.tasks)
        )

        truncated = False

        if not terminated:

            next_task = self.tasks[
                self.task_index
            ]

            self.env.set_task(
                next_task
            )

            observation = (
                self.env.get_state()
            )

        else:

            observation = np.zeros(
                self.observation_space.shape,
                dtype=np.float32
            )

        info = {
            "success": success,
            "latency": result["latency"],
            "energy": (
                result.get(
                    "energy",
                    0.0
                )
            ),
            "server_id": action
        }

        return (
            observation,
            reward,
            terminated,
            truncated,
            info
        )