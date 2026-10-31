# Per-sensor energy preservation: background and design

> **Update (branch `feature/sensor-energy`):** this design is now implemented in `env/sensors.py`, `agents/baselines.py::LyapunovGreedy` and `experiments/sensor_energy.py`. Results are in `results/sensor_energy/<regime>/table.md` and summarised in README §8.3.

## Why it fits this project
The paper motivates EdgePlus with battery-powered air-quality sensors on lampposts (Sec. I), but its energy model only constrains **mobile servers** (Eq. 3). The sensors' own batteries are never modelled. Our simulator does the same: `energy_required()` includes the upload energy P_tx·L_tx, but charges it to no device.

## What the literature does (paraphrased)
- **Lyapunov "virtual energy queue".** A long-term energy limit is turned into a queue that must stay stable. Each slot then minimises drift + V·penalty. LODCO (Mao et al.) uses this for devices with energy harvesting, jointly choosing offloading, CPU frequency and transmit power ([arXiv 1605.05488](https://arxiv.org/html/1605.05488v1)). The same virtual-queue trick appears in wireless-powered MEC ([MDPI Mathematics 12(16) 2478](https://www.mdpi.com/2227-7390/12/16/2478/xml)) and in solar-powered sensor networks ([MDPI Appl. Sci. 13(8) 4966](https://www.mdpi.com/2076-3417/13/8/4966)).
- **RL with the battery level in the state.** An IoT device chooses which edge server to offload to, and how much, using its current battery level, the observed bandwidth and the predicted harvested energy ([Min et al., arXiv 1712.08768](https://arxiv.org/html/1712.08768v1)).
- **Wireless-powered MEC with DRL** (DROO): devices are charged by RF and a DRL policy decides offloading online ([Huang et al., arXiv 1808.01977](https://arxiv.org/html/1808.01977v5)).
- **Energy vs delay trade-off**, also solved per slot with Lyapunov decomposition ([arXiv 2202.03648](https://arxiv.org/html/2202.03648v1)).

## Proposed extension for EdgePlus (design)
1. **Sensors as entities.** For example 200 sensors (the paper's dataset has 449 sites), each with a home cluster, battery capacity B_j, battery level b_j(t), and solar harvest h_j(t) (day/night profile).
2. **Who pays what.** The sensor pays the upload: E_j = P_tx · b_i / R̄_{i,s}. The choice of server changes this through the link rate, so a slow link (low gain, far mobile, cloud backhaul) drains the sensor more. Servers keep paying compute and movement energy.
3. **Feasibility (mask).** A server is infeasible if b_j(t) < E_j, so the sensor cannot afford the upload. This is a new constraint next to the existing ones in `feasibility_reasons()`.
4. **Long-term preservation (Lyapunov).** Keep a virtual queue per sensor, Z_j(t+1) = max(Z_j(t) + E_j(t) − ē_j, 0), where ē_j is the energy the sensor can spend per task and still last a target lifetime. Add −λ_E·Z_j·E_j to the reward (or as an advisory logit bias). Sensors that are spending too fast then push the policy toward cheap uploads.
5. **Metrics.** Network lifetime (time until the first or the 10 % sensor dies), tasks lost to empty batteries, Jain fairness of remaining battery, plus the usual success and latency.
6. **Experiment.** Masked CCPPO with and without the battery mask and the Z-term, at medium and stress load, on the same 5 seeds. Expected trade-off [HYPOTHESIS]: longer lifetime in exchange for slightly higher latency, because cheaper links are not always the fastest.

Rough size: one `sensors.py` module, about 40 lines in `edge_env.py`, a reward term, about 6 tests, and one runner. This is similar in size to the ledger feedback.
