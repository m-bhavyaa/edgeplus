"""PID utilisation controller with Ziegler-Nichols init and Jury certification
(paper Eq. 11, 17, 39-40, Sec. V-F).

Runtime: one PID per cluster, e_c = rho_c - rho_set, u_c clipped to [-1, 1].
SIGN CONVENTION (paper leaves it implicit): an overloaded cluster (e > 0) should
become LESS attractive, so the logit bias is  -lambda_P * u_c.

Offline (OBJ6): FOPDT plant G(s) = K e^{-Ls} / (tau s + 1), ZOH-discretised at Ts;
discrete PID C(z) = Kp + Ki*Ts/(1 - z^-1) + Kd*(1 - z^-1)/Ts; stability of
1 + C(z)G(z) = 0 checked with the Jury (Schur-Cohn) test over all 8 corners of
the +/-20 % gain box; settling time (2 % band) and overshoot from a step simulation.
"""

from __future__ import annotations

import itertools

import numpy as np


class PID:
    def __init__(self, kp: float, ki: float, kd: float, dt: float, i_limit: float = 5.0):
        self.kp, self.ki, self.kd, self.dt, self.i_limit = kp, ki, kd, dt, i_limit
        self.integral = 0.0
        self.prev = None

    def step(self, error: float) -> float:
        self.integral = float(np.clip(self.integral + error * self.dt, -self.i_limit, self.i_limit))
        deriv = 0.0 if self.prev is None else (error - self.prev) / self.dt
        self.prev = error
        return float(np.clip(self.kp * error + self.ki * self.integral + self.kd * deriv, -1, 1))


# ------------------------------------------------------------------ offline tools

def ziegler_nichols_fopdt(K: float, tau: float, L: float) -> tuple:
    """Classic ZN open-loop (reaction-curve) PID rules."""
    kp = 1.2 * tau / (K * L)
    ti, td = 2.0 * L, 0.5 * L
    return kp, kp / ti, kp * td


def fopdt_discrete(K, tau, L, Ts):
    """ZOH discretisation. Returns (num, den) as polynomials in z^-1."""
    a = np.exp(-Ts / tau)
    d = int(round(L / Ts))
    num = np.zeros(d + 2)
    num[d + 1] = K * (1 - a)
    return num, np.array([1.0, -a])


def pid_discrete(kp, ki, kd, Ts):
    """C(z) as (num, den) in z^-1:  [(kp+ki Ts+kd/Ts) - (kp+2kd/Ts) z^-1 + (kd/Ts) z^-2] / (1 - z^-1)."""
    num = np.array([kp + ki * Ts + kd / Ts, -(kp + 2 * kd / Ts), kd / Ts])
    return num, np.array([1.0, -1.0])


def closed_loop_poly(plant, ctrl) -> np.ndarray:
    """Characteristic polynomial den_c*den_p + num_c*num_p (in z^-1, = coeffs of z^n)."""
    a = np.convolve(ctrl[1], plant[1])   # convolve keeps leading zeros (polymul trims them)
    b = np.convolve(ctrl[0], plant[0])
    n = max(len(a), len(b))
    return np.pad(a, (0, n - len(a))) + np.pad(b, (0, n - len(b)))


def jury_stable(coeffs) -> bool:
    """Jury / Schur-Cohn test: all roots of sum coeffs[k] z^(n-k) strictly inside |z|=1."""
    c = np.trim_zeros(np.asarray(coeffs, float), "b")
    while len(c) > 1:
        if abs(c[-1]) >= abs(c[0]):
            return False
        c = (c[0] * c - c[-1] * c[::-1])[:-1]
    return True


def step_response(kp, ki, kd, K, tau, L, Ts, horizon=90.0, umax=100.0):
    """Unit-step closed-loop simulation; returns (t, y)."""
    a = np.exp(-Ts / tau)
    d = int(round(L / Ts))
    n = int(horizon / Ts)
    y, u_hist = np.zeros(n), np.zeros(n + d + 1)
    integral, prev = 0.0, None
    for k in range(1, n):
        e = 1.0 - y[k - 1]
        integral = float(np.clip(integral + e * Ts, -umax, umax))   # anti-windup clamp
        deriv = 0.0 if prev is None else (e - prev) / Ts
        prev = e
        u = float(np.clip(kp * e + ki * integral + kd * deriv, -umax, umax))
        u_hist[k] = u
        u_del = u_hist[k - d - 1] if k - d - 1 >= 0 else 0.0
        y[k] = a * y[k - 1] + K * (1 - a) * u_del
    return np.arange(n) * Ts, y


def step_metrics(t, y, band=0.02):
    mp = max(0.0, (y.max() - 1.0) * 100)
    outside = np.flatnonzero(np.abs(y - 1.0) > band)
    ts = float(t[outside[-1] + 1]) if len(outside) and outside[-1] + 1 < len(t) else (
        0.0 if not len(outside) else float("inf"))
    return ts, mp


def robustness_check(kp, ki, kd, K, tau, L, Ts, drift=0.2, ts_max=10.0, mp_max=15.0):
    """Evaluate nominal gains and all 2^3 corners of the +/-drift box (Eq. 17/40)."""
    plant = fopdt_discrete(K, tau, L, Ts)
    rows = []
    for dp, di, dd in [(0, 0, 0)] + list(itertools.product((-drift, drift), repeat=3)):
        g = (kp * (1 + dp), ki * (1 + di), kd * (1 + dd))
        stable = jury_stable(closed_loop_poly(plant, pid_discrete(*g, Ts)))
        ts, mp = step_metrics(*step_response(*g, K, tau, L, Ts)) if stable else (float("inf"), float("inf"))
        rows.append({"kp": g[0], "ki": g[1], "kd": g[2], "stable": stable, "Ts": ts, "Mp": mp,
                     "pass": stable and ts <= ts_max and mp <= mp_max})
    return rows
