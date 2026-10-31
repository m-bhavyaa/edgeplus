"""Per-task feasibility diagnostics (works on the current simulator).

For the offered task, counts how many *routable* servers fail each constraint,
how many fail two or more at once, and a primary reason for zero-feasible
tasks. Primary-reason precedence (documented assumption, summary label only):
the most common first-failed constraint among routable servers, in the order
slice > memory > energy > reputation > deadline. All counts are kept separately.
"""

from __future__ import annotations

from collections import Counter

from env.edge_env import CONSTRAINTS

PRECEDENCE = ("slice", "memory", "energy", "reputation", "deadline")


def diagnose_task(core, task) -> dict:
    rows = [core.feasibility_reasons(task, s) for s in core.servers]
    routable = [r for r in rows if r["routing"]]
    out = {"n_feasible": sum(r["feasible"] for r in rows), "n_routable": len(routable)}
    for c in CONSTRAINTS:
        if c != "routing":
            out[f"rej_{c}"] = sum(not r[c] for r in routable)
    out["n_multi_fail"] = sum(sum(not r[c] for c in PRECEDENCE) >= 2 for r in routable)
    firsts = [next(c for c in PRECEDENCE if not r[c]) for r in routable if not r["feasible"]]
    out["primary_reason"] = (Counter(firsts).most_common(1)[0][0]
                             if out["n_feasible"] == 0 and firsts else "")
    return out
