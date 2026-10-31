"""Small statistics helpers (no SciPy dependency).

- mean, std (ddof=1), 95 % t-interval across seeds
- paired sign-flip permutation test across seeds (exact for n <= 12).
  With 5 seeds the smallest possible two-sided p is 2/32 = 0.0625, so seed-level
  tests cannot reach p < 0.05; this is stated in the report.
- McNemar test on per-task on-time outcomes for two policies on the SAME
  workload (normal approximation with continuity correction).
"""

from __future__ import annotations

import itertools
import math

import numpy as np

_T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
         8: 2.306, 9: 2.262, 10: 2.228, 15: 2.131, 20: 2.086, 30: 2.042}


def t975(df: int) -> float:
    if df in _T975:
        return _T975[df]
    return _T975[min(_T975, key=lambda k: abs(k - df))] if df < 30 else 1.96


def mean_ci(xs) -> dict:
    xs = np.asarray(xs, float)
    n = len(xs)
    m = float(xs.mean())
    sd = float(xs.std(ddof=1)) if n > 1 else 0.0
    h = t975(n - 1) * sd / math.sqrt(n) if n > 1 else 0.0
    return {"mean": m, "std": sd, "ci95_low": m - h, "ci95_high": m + h, "n": n}


def paired_permutation_p(a, b) -> float:
    d = np.asarray(a, float) - np.asarray(b, float)
    obs = abs(d.mean())
    if len(d) > 12:
        raise ValueError("exact permutation limited to n <= 12")
    count = total = 0
    for signs in itertools.product((1, -1), repeat=len(d)):
        total += 1
        count += abs((d * signs).mean()) >= obs - 1e-12
    return count / total


def mcnemar_p(success_a, success_b) -> float:
    a, b = np.asarray(success_a, bool), np.asarray(success_b, bool)
    n01 = int(np.sum(~a & b))
    n10 = int(np.sum(a & ~b))
    if n01 + n10 == 0:
        return 1.0
    z = (abs(n01 - n10) - 1) / math.sqrt(n01 + n10)
    return float(math.erfc(max(z, 0) / math.sqrt(2)))
