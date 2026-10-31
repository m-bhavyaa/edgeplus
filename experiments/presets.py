"""Named configuration presets (dotted-key overrides of configs/base.json).

BASELINE: what M6-M8 run on: paper-aligned simulator, NO ledger feedback,
NO advisory, NO consensus. Masks are a property of the policy (M7 ignores them).

ABLATIONS (paper Table VI) for the integrated system:
    A1 full   masks + advisory + PSO + ledger
    A2 no PSO           A3 no advisory      A4 no ledger
    A5 no masks         A6 plain CCPPO (nothing)
"Masks" here means the policy samples from the masked softmax. When masks are
off the policy samples over all routable-or-not servers and an infeasible
choice is rejected (outcome rejected_infeasible_action).
"""

BASELINE = {"ledger.enabled": False, "consensus.mode": "off", "advisory.enabled": False}

ABLATIONS = {
    "A1_full":        {"masks": True,  "advisory": True,  "pso": True,  "ledger": True},
    "A2_no_pso":      {"masks": True,  "advisory": True,  "pso": False, "ledger": True},
    "A3_no_advisory": {"masks": True,  "advisory": False, "pso": True,  "ledger": True},
    "A4_no_ledger":   {"masks": True,  "advisory": True,  "pso": True,  "ledger": False},
    "A5_no_masks":    {"masks": False, "advisory": True,  "pso": True,  "ledger": True},
    "A6_plain":       {"masks": False, "advisory": False, "pso": False, "ledger": False},
}

# M14: consensus-delay ablations, all on top of the integrated (A2-style) system.
CONSENSUS_VARIANTS = {
    "C0_no_consensus":        {"consensus.mode": "off"},
    "C1_edge_report_only":    {"consensus.mode": "report_only", "consensus.path": "edge"},
    "C2_edge_mask_aware":     {"consensus.mode": "mask_aware", "consensus.path": "edge"},
    "C3_cloud_report_only":   {"consensus.mode": "report_only", "consensus.path": "edge_cloud"},
    "C4_cloud_mask_aware":    {"consensus.mode": "mask_aware", "consensus.path": "edge_cloud"},
}
