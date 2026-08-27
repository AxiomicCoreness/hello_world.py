"""Conversation-tree merge. Extends worker_tree; does not rewrite 9027 body."""

PARENT = "commander"
EXTENDS_WORKER_TREE = "9027"

BRANCHES = [
    {"id": "fusion_515", "kind": "sealed_body"},
    {"id": "hyperion_516", "kind": "sealed_body"},
    {"id": "worker_tree_9025_9027", "kind": "config"},
    {"id": "october39_9040", "kind": "code_literal"},
    {"id": "fleck_split_9042", "kind": "vision_code_frequency"},
    {"id": "entropy_rate_9043", "kind": "144_phi4"},
    {"id": "lumeris_9044_9045", "kind": "name_seal"},
    {"id": "schema_0429_9046", "kind": "schema"},
    {"id": "integrity_9047", "kind": "enumerated_score"},
    {"id": "deepseek_rate_9048_9051", "kind": "alpha_eff_0"},
    {"id": "era_ignore_9049", "kind": "policy"},
    {"id": "anthropic_alias_strip_9050", "kind": "adapter_prefer"},
    {"id": "q8_24_8197", "kind": "yaml_plus_broadcast_json"},
    {"id": "policy_9055_9056", "kind": "lead_diagnostic"},
]

LEAD = {
    "oidc_client_credentials": False,
    "cron_6h": False,
    "restart_from_here": False,
    "alpha_eff": 0.0,
    "folded_offline": False,
}


def merge():
    return {
        "parent": PARENT,
        "extends": EXTENDS_WORKER_TREE,
        "branches": BRANCHES,
        "lead": LEAD,
        "fusion_canonical": 515,
        "hyperion_preserved": 516,
    }
