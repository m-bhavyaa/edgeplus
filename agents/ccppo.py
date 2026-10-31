"""M9: masked cooperative PPO with a centralized critic (CCPPO), CTDE style.

What the paper specifies (Sec. III-E, III-J, IV-E2, Eq. 8, 10):
  * a cooperative multi-actor policy {pi_theta_j} with ONE shared value V_psi(s)
  * actors are "cluster-aware" and see only LOCAL observations at inference;
    the critic is trained on GLOBAL context
  * masked softmax (Eq. 10), GAE, clipped ratio, entropy bonus, optional KL
    penalty, gradient clipping; advisory bias added to logits (Eq. 9)

What the paper does NOT specify, and our documented choices:
  * agents: one actor per cluster (A = 10). The actor of cluster c decides the
    tasks that arrive in c. Tasks arrive one at a time, so at each step exactly
    one actor acts and the joint action is that actor's action.
  * parameter sharing: all actors share one network that receives a one-hot
    cluster id (common in MAPPO-style CTDE; keeps 10 actors trainable on CPU).
  * local observation: task features + features of the actor's K candidate
    servers in routing order (local stationary, local mobile, neighbour mobiles,
    cloud), zero-padded to K slots.
  * global state for the critic: full server state + all cluster loads.
  * reward: shared team reward = the env reward of the step (Eq. 7 + ledger
    shaping); rewards of tasks rejected between two decisions are added to the
    previous decision.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

from advisory import AdvisoryLayer
from env.factory import make_core
from env.task_generator import TaskGenerator


def candidate_table(core) -> tuple[np.ndarray, int]:
    """cand[c, k] = server id of slot k for actor c (or -1), in routing order."""
    C = core.cfg["workload"]["num_clusters"]
    rows = []
    for c in range(C):
        probe = type("T", (), {"cluster": c})()
        ranked = sorted((core.routing_region(probe, s), s.id) for s in core.servers
                        if core.routing_region(probe, s) is not None)
        rows.append([sid for _, sid in ranked])
    K = max(len(r) for r in rows)
    return np.array([r + [-1] * (K - len(r)) for r in rows]), K


def mlp(inp, hid, out):
    return nn.Sequential(nn.Linear(inp, hid), nn.Tanh(), nn.Linear(hid, hid), nn.Tanh(),
                         nn.Linear(hid, out))


class CCPPO:
    """Shared cluster-aware actor + centralized critic."""

    def __init__(self, cfg: dict, use_masks: bool = True, use_advisory: bool = True,
                 seed: int = 0, name: str = "m9_ccppo"):
        self.cfg, self.use_masks, self.name = cfg, use_masks, name
        self.use_advisory = use_advisory
        torch.manual_seed(seed)
        self.rng = np.random.default_rng(seed)
        probe = make_core(cfg)
        self.cand, self.K = candidate_table(probe)
        self.C = self.cand.shape[0]
        self.tdim, self.sdim = probe.task_feat_dim, probe.server_feat_dim
        self.local_dim = self.tdim + self.C + self.sdim * self.K
        self.global_dim = probe.state_dim + self.C
        h = cfg["ccppo"]["hidden"]
        self.actor = mlp(self.local_dim, h, self.K)
        self.critic = mlp(self.global_dim, 2 * h, 1)
        self.advisory = AdvisoryLayer(cfg["advisory"], self.C) if use_advisory else None
        self.energy_bias = 0.0   # extension: Lyapunov logit bias weight (0 = off)

    # ----------------------------------------------------------- observations
    def local_obs(self, core, task) -> np.ndarray:
        f = core.task_features(task) + [float(task.cluster == c) for c in range(self.C)]
        for sid in self.cand[task.cluster]:
            f += core.server_features(task, core.servers[sid]) if sid >= 0 else [0.0] * self.sdim
        return np.array(f, np.float32)

    def global_state(self, core) -> np.ndarray:
        loads = [core.cluster_load(c) for c in range(self.C)]
        return np.concatenate([core.get_state(), np.array(loads, np.float32)])

    def slot_mask(self, task, mask: np.ndarray) -> np.ndarray:
        ids = self.cand[task.cluster]
        valid = ids >= 0
        if not self.use_masks:
            return valid                       # only padding is removed
        return valid & np.where(valid, mask[np.maximum(ids, 0)], False)

    def slot_bias(self, core, task) -> np.ndarray:
        ids = self.cand[task.cluster]
        b = self.advisory.bias(core) if self.advisory is not None else np.zeros(len(core.servers))
        if self.energy_bias > 0 and core.sensors is not None:   # -w * Z_j * E_up / e_ref
            b = b - self.energy_bias * np.array([core.lyapunov_price(task, s) for s in core.servers])
        return np.where(ids >= 0, b[np.maximum(ids, 0)], 0.0).astype(np.float32)

    def _dist(self, obs, bias, smask):
        logits = self.actor(obs) + bias                       # Eq. 9
        logits = logits.masked_fill(~smask, -1e9)             # Eq. 10
        return torch.distributions.Categorical(logits=logits)

    # ------------------------------------------------------------- inference
    def reset(self, core):
        if self.advisory is not None:
            self.advisory.reset()

    @torch.no_grad()
    def act(self, core, mask) -> int:
        """Evaluator interface (deterministic, decentralized: local obs only)."""
        task = core.current_task
        sm = self.slot_mask(task, mask)
        d = self._dist(torch.as_tensor(self.local_obs(core, task))[None],
                       torch.as_tensor(self.slot_bias(core, task))[None],
                       torch.as_tensor(sm)[None])
        return int(self.cand[task.cluster][int(d.probs.argmax())])

    # -------------------------------------------------------------- training
    def train(self, timesteps: int, log_path: Path | None = None) -> list[dict]:
        hp, cfg = self.cfg["ccppo"], self.cfg
        opt = torch.optim.Adam(list(self.actor.parameters()) + list(self.critic.parameters()),
                               lr=hp["lr"])
        core = make_core(cfg)
        episode, steps, log = 0, 0, []
        buf = {k: [] for k in ("obs", "gs", "bias", "sm", "a", "logp", "v", "r", "done")}
        tasks, idx = [], 0
        ep_ret, ep_ok, ep_n, t0 = 0.0, 0, 0, time.time()

        def new_episode():
            nonlocal tasks, idx, episode
            seed = cfg["seeds"]["train_base"] + 500 + episode
            core.reset(seed)
            self.reset(core)
            tasks = TaskGenerator(cfg["workload"], seed).generate_episode(cfg["train_tasks_per_episode"])
            idx, episode = 0, episode + 1

        new_episode()
        while steps < timesteps:
            task = tasks[idx]
            core.set_task(task)
            mask = core.get_action_mask()
            sm = self.slot_mask(task, mask)
            if not mask.any():
                res = core.reject()      # explicit, no decision (same rule as the evaluator)
                if buf["r"]:
                    buf["r"][-1] += res["reward"]
            else:
                obs = self.local_obs(core, task)
                gs = self.global_state(core)
                bias = self.slot_bias(core, task)
                with torch.no_grad():
                    d = self._dist(torch.as_tensor(obs)[None], torch.as_tensor(bias)[None],
                                   torch.as_tensor(sm)[None])
                    a = d.sample()
                    v = self.critic(torch.as_tensor(gs)[None]).item()
                res = core.execute(int(self.cand[task.cluster][a.item()]))
                for k, x in (("obs", obs), ("gs", gs), ("bias", bias), ("sm", sm), ("a", a.item()),
                             ("logp", d.log_prob(a).item()), ("v", v), ("r", res["reward"]),
                             ("done", False)):
                    buf[k].append(x)
                steps += 1
            ep_ret += res["reward"]
            ep_ok += res["success"]
            ep_n += 1
            idx += 1
            if idx >= len(tasks):
                if buf["done"]:
                    buf["done"][-1] = True
                log.append({"episode": episode, "steps": steps, "return": ep_ret,
                            "success": ep_ok / ep_n, "seconds": time.time() - t0})
                ep_ret, ep_ok, ep_n = 0.0, 0, 0
                new_episode()
            if len(buf["a"]) >= hp["n_steps"]:
                self._update(buf, opt, core, tasks, idx)
                buf = {k: [] for k in buf}
        if log_path:
            Path(log_path).write_text(json.dumps(log, indent=1))
        return log

    def _update(self, buf, opt, core, tasks, idx):
        hp = self.cfg["ccppo"]
        r, v, done = np.array(buf["r"]), np.array(buf["v"]), np.array(buf["done"])
        # bootstrap from the next state's value unless the buffer ended an episode
        last_v = 0.0
        if not done[-1] and idx < len(tasks):
            with torch.no_grad():
                last_v = self.critic(torch.as_tensor(self.global_state(core))[None]).item()
        adv, gae = np.zeros_like(r), 0.0
        for t in reversed(range(len(r))):                     # GAE
            nv = last_v if t == len(r) - 1 else v[t + 1]
            nonterm = 0.0 if done[t] else 1.0
            delta = r[t] + hp["gamma"] * nv * nonterm - v[t]
            gae = delta + hp["gamma"] * hp["gae_lambda"] * nonterm * gae
            adv[t] = gae
        ret = adv + v
        T = {k: torch.as_tensor(np.array(buf[k])) for k in ("obs", "gs", "bias", "sm", "a", "logp")}
        A = torch.as_tensor((adv - adv.mean()) / (adv.std() + 1e-8), dtype=torch.float32)
        R = torch.as_tensor(ret, dtype=torch.float32)
        n = len(r)
        for _ in range(hp["epochs"]):
            for mb in np.array_split(self.rng.permutation(n), max(1, n // hp["minibatch"])):
                d = self._dist(T["obs"][mb], T["bias"][mb], T["sm"][mb])
                logp = d.log_prob(T["a"][mb])
                ratio = torch.exp(logp - T["logp"][mb].float())
                a_mb = A[mb]
                l_clip = -torch.min(ratio * a_mb,
                                    torch.clamp(ratio, 1 - hp["clip"], 1 + hp["clip"]) * a_mb).mean()
                kl = (T["logp"][mb].float() - logp).mean()        # approx KL(old || new)
                l_actor = l_clip + hp["kl_coef"] * kl - hp["ent_coef"] * d.entropy().mean()  # Eq. 8
                l_critic = ((self.critic(T["gs"][mb]).squeeze(-1) - R[mb]) ** 2).mean()
                opt.zero_grad()
                (l_actor + hp["vf_coef"] * l_critic).backward()
                nn.utils.clip_grad_norm_(list(self.actor.parameters()) + list(self.critic.parameters()),
                                         hp["max_grad_norm"])
                opt.step()

    # ------------------------------------------------------------- save/load
    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"actor": self.actor.state_dict(), "critic": self.critic.state_dict(),
                    "use_masks": self.use_masks, "use_advisory": self.use_advisory,
                    "K": self.K}, path)

    @classmethod
    def load(cls, path: Path, cfg: dict, name: str | None = None) -> "CCPPO":
        ck = torch.load(path, weights_only=False)
        obj = cls(cfg, ck["use_masks"], ck["use_advisory"], name=name or Path(path).stem)
        obj.actor.load_state_dict(ck["actor"])
        obj.critic.load_state_dict(ck["critic"])
        return obj
