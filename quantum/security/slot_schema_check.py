#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stdlib slot-schema check. No PyYAML.

Does not replace quantum/security/__init__.py.
Canonical file: docs/luminara_slot.yaml.
Missing file is PENDING, not a pass.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

POLICY_WARNING_PATH = "quantum/security/POLICY_WARNING.md"
CANONICAL_SLOT_FILE = "docs/luminara_slot.yaml"
POLICY_WARNING_TEXT = (
    "WARNING: A missing slot file is not a pass; the only slot file is docs/luminara_slot.yaml;\n"
    "role, holder, and channel are nested under slots; gamma, lambda, log, and filled_by stay null;\n"
    "the live bind is 0.0.0.0 with PORT default 380; sovereign_automaton_10_06() takes no text;\n"
    "do not overwrite super_symplectic.py with a slot checker; do not print secrets."
)

ALLOWED_TOP = {
    "name",
    "status",
    "prior_uses_not_definitions",
    "slots",
    "endpoint_proposed",
    "live_bind_note",
    "callable",
    "text_consumed",
    "filled_by",
    "commit_identity",
}


def print_policy_warning() -> None:
    print(POLICY_WARNING_TEXT, flush=True)


def parse_yaml_to_xml_string(raw_yaml_text: str) -> str:
    """Indent-aware line split. Not a YAML parser. Lists without a colon are skipped."""
    root = ET.Element("repository")
    slots_node = ET.SubElement(root, "slots")
    for line in raw_yaml_text.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, _, value = line.strip().partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if value.lower() in {"null", "~"}:
            value = ""
        parent = slots_node if line[:1].isspace() else root
        if parent is root and key == "slots":
            continue
        ET.SubElement(parent, key).text = value
    return ET.tostring(root, encoding="utf-8").decode("utf-8")


def get_security_status(repo_path: str = ".") -> dict[str, str | bool]:
    print_policy_warning()
    status_report: dict[str, str | bool] = {
        "policy_warning": POLICY_WARNING_TEXT,
        "canonical_slot_path": CANONICAL_SLOT_FILE,
        "schema_state": "UNKNOWN",
        "listeners_active": False,
        "pyyaml": False,
    }
    target = os.path.join(repo_path, CANONICAL_SLOT_FILE)
    if not os.path.exists(target):
        status_report["schema_state"] = "PENDING"
        return status_report
    try:
        with open(target, "r", encoding="utf-8") as handle:
            raw = handle.read()
        root = ET.fromstring(parse_yaml_to_xml_string(raw))
        for child in root:
            if child.tag not in ALLOWED_TOP:
                status_report["schema_state"] = "FAIL"
                return status_report
        slots = root.find("slots")
        if slots is None:
            status_report["schema_state"] = "FAIL"
            return status_report
        role = slots.find("role")
        holder = slots.find("holder")
        channel = slots.find("channel")
        if role is None or role.text != "chat":
            status_report["schema_state"] = "FAIL"
            return status_report
        if holder is None or holder.text != "sovereign_automaton_10.06":
            status_report["schema_state"] = "FAIL"
            return status_report
        if channel is None or channel.text != "/mcp/tool":
            status_report["schema_state"] = "FAIL"
            return status_report
        for field in ("gamma", "lambda", "log"):
            node = slots.find(field)
            if node is not None and node.text:
                status_report["schema_state"] = "FAIL"
                return status_report
        filled = root.find("filled_by")
        if filled is not None and filled.text:
            status_report["schema_state"] = "FAIL"
            return status_report
        status_report["schema_state"] = "PASS"
    except Exception:
        status_report["schema_state"] = "FAIL"
    return status_report


if __name__ == "__main__":
    report = get_security_status(sys.argv[2] if len(sys.argv) > 2 else ".")
    print(report["schema_state"])
    if report["schema_state"] == "FAIL":
        sys.exit(1)
