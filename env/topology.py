from dataclasses import dataclass
import math


@dataclass
class Cluster:
    id: int
    x: float
    y: float


class Topology:

    def __init__(self):
        self.clusters = self._create_clusters()
        self.neighbors = self._create_neighbors()

    def _create_clusters(self):

        positions = {
            0: (0.0, 0.0),
            1: (2.0, 0.0),
            2: (4.0, 0.0),
            3: (0.0, 2.0),
            4: (2.0, 2.0),
            5: (4.0, 2.0),
            6: (0.0, 4.0),
            7: (2.0, 4.0),
            8: (4.0, 4.0),
            9: (6.0, 2.0),
        }

        return {
            cluster_id: Cluster(
                id=cluster_id,
                x=x,
                y=y
            )
            for cluster_id, (x, y) in positions.items()
        }

    def _create_neighbors(self):

        return {
            0: [1, 3],
            1: [0, 2, 4],
            2: [1, 5],
            3: [0, 4, 6],
            4: [1, 3, 5, 7],
            5: [2, 4, 8, 9],
            6: [3, 7],
            7: [4, 6, 8],
            8: [5, 7, 9],
            9: [5, 8],
        }

    def get_neighbors(self, cluster_id):
        return self.neighbors[cluster_id]

    def distance(self, cluster_a, cluster_b):

        a = self.clusters[cluster_a]
        b = self.clusters[cluster_b]

        return math.sqrt(
            (a.x - b.x) ** 2 +
            (a.y - b.y) ** 2
        )

    def are_neighbors(self, cluster_a, cluster_b):

        return cluster_b in self.neighbors[cluster_a]