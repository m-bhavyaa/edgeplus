"""Leader election (paper Sec. III-F):
score_s = w1 * (1 - load_ratio_s) + w2 * energy_ratio_s, leader_c = argmax over servers of c.
load_ratio_s = min(1, backlog_s / 10 s) (ASSUMPTION); energy_ratio = 1 for non-mobiles."""

from __future__ import annotations

from env.server import MOBILE


def elect_leaders(core, w1: float, w2: float) -> dict:
    best: dict = {}
    for s in core.servers:
        if s.cluster < 0:
            continue
        load = min(1.0, s.backlog(core.time) / 10.0)
        energy = s.available_energy / s.energy_budget if s.kind == MOBILE else 1.0
        score = w1 * (1 - load) + w2 * energy
        if s.cluster not in best or score > best[s.cluster][0]:
            best[s.cluster] = (score, s.id)
    return {c: sid for c, (_, sid) in best.items()}
