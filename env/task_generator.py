import numpy as np

from .task import Task


class TaskGenerator:

    def __init__(
        self,
        num_clusters=10,
        seed=42
    ):
        self.num_clusters = num_clusters
        self.rng = np.random.default_rng(seed)

    def generate_task(
        self,
        task_id,
        arrival_time=None
    ):

        if arrival_time is None:
            arrival_time = float(
                self.rng.uniform(0, 100)
            )

        cluster = int(
            self.rng.integers(
                0,
                self.num_clusters
            )
        )

        service_class = self.rng.choice(
            ["URLLC", "eMBB", "mMTC"]
        )

        if service_class == "URLLC":

            cpu_cycles = self.rng.uniform(
                1e9,
                4e9
            )

            memory = self.rng.uniform(
                256,
                1024
            )

            payload = self.rng.uniform(
                0.5e6,
                2e6
            )

            deadline_window = self.rng.uniform(
                1,
                5
            )

            priority = 3.0

        elif service_class == "eMBB":

            cpu_cycles = self.rng.uniform(
                2e9,
                8e9
            )

            memory = self.rng.uniform(
                512,
                2048
            )

            payload = self.rng.uniform(
                5e6,
                20e6
            )

            deadline_window = self.rng.uniform(
                5,
                15
            )

            priority = 2.0

        else:

            cpu_cycles = self.rng.uniform(
                0.5e9,
                2e9
            )

            memory = self.rng.uniform(
                128,
                512
            )

            payload = self.rng.uniform(
                0.1e6,
                1e6
            )

            deadline_window = self.rng.uniform(
                10,
                30
            )

            priority = 1.0

        deadline = (
            arrival_time
            + deadline_window
        )

        return Task(
            id=task_id,
            arrival_time=arrival_time,
            deadline=deadline,
            cluster=cluster,
            service_class=service_class,
            cpu_cycles=cpu_cycles,
            memory=memory,
            payload=payload,
            priority=priority
        )

    def generate_batch(
        self,
        num_tasks
    ):

        tasks = []

        for task_id in range(num_tasks):

            task = self.generate_task(
                task_id=task_id
            )

            tasks.append(task)

        tasks.sort(
            key=lambda task: task.arrival_time
        )

        return tasks