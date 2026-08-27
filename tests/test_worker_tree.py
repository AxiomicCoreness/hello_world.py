#!/usr/bin/env python3
from garden_surgery.worker_tree import (
    TREE_VERSION,
    children_of,
    lineage,
    load_contract,
    node,
    parent_of,
    siblings_of,
    tree_payload,
)


def test_parent_sibling_edges():
    assert parent_of("declaration_flag") == "commander"
    assert parent_of("commander") is None
    assert parent_of("diagnostic_json") == "declaration_flag"
    sibs = siblings_of("declaration_flag")
    assert "hyperion_0516" in sibs
    assert "trigger_excavate" in sibs
    assert "declaration_flag" not in sibs
    assert "diagnostic_htmx" in siblings_of("diagnostic_json")
    assert "workers_tree" in siblings_of("health")


def test_children_and_lineage():
    kids = children_of("declaration_flag")
    assert "diagnostic_json" in kids
    assert "workers_tree" in kids
    assert "worker_node" in kids
    assert children_of("commander")[0] == "theorems"
    assert lineage("diagnostic_htmx") == [
        "commander",
        "declaration_flag",
        "diagnostic_htmx",
    ]
    assert lineage("hyperion_0516") == ["commander", "hyperion_0516"]
    assert lineage("commander") == ["commander"]
    assert lineage("no_such_worker") == []


def test_tree_does_not_claim_live_swarm():
    t = tree_payload()
    assert t["version"] == TREE_VERSION == "9027"
    assert node("anomaly_distance")["narrative"] == 8356
    assert t["instantiates_144008_processes"] is False
    assert t["fusion_canonical"] == 515
    assert t["hyperion_preserved"] == 516
    assert t["mcp"] is False
    assert node("hyperion_0516")["preserved"] is True
    assert "parent_of" in t["edges"]
    assert t["edges"]["parent_of"]["hyperion_0516"] == "commander"


def test_contract_extends_9025():
    c = load_contract()
    assert c["present"] is True
    assert c["version"] in {"9026", "9027"}
    assert c["extends"] in {"9025", "9026"}


if __name__ == "__main__":
    test_parent_sibling_edges()
    test_children_and_lineage()
    test_tree_does_not_claim_live_swarm()
    test_contract_extends_9025()
    print("test_worker_tree: PASS")
