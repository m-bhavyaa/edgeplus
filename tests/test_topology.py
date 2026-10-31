"""M1: topology correctness."""

import math
from collections import deque

from env.topology import Topology


def test_ten_clusters_with_valid_neighbor_indices():
    t = Topology()
    assert sorted(t.clusters) == list(range(10))
    for c, ns in t.neighbors.items():
        assert c not in ns, "no self-loops"
        assert all(n in t.clusters for n in ns)
        assert len(ns) == len(set(ns)), "no duplicate neighbors"


def test_adjacency_is_symmetric():
    t = Topology()
    for a, ns in t.neighbors.items():
        for b in ns:
            assert t.are_neighbors(b, a), f"{a}->{b} but not {b}->{a}"


def test_graph_is_connected():
    t = Topology()
    seen, q = {0}, deque([0])
    while q:
        for n in t.get_neighbors(q.popleft()):
            if n not in seen:
                seen.add(n)
                q.append(n)
    assert seen == set(range(10))


def test_distance_is_euclidean_and_symmetric():
    t = Topology()
    assert t.distance(0, 1) == 2.0
    assert math.isclose(t.distance(0, 4), math.sqrt(8))
    for a in range(10):
        assert t.distance(a, a) == 0.0
        for b in range(10):
            assert t.distance(a, b) == t.distance(b, a)
