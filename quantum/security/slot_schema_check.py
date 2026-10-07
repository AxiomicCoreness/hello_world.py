#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stdlib slot-file schema checker. No PyYAML.

Indentation-driven YAML subset. Missing file is PENDING and exits 2.
"""
from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

CANONICAL_SLOT_FILE = "docs/luminara_slot.yaml"
POLICY_WARNING_TEXT = (
    "WARNING: A missing slot file is not a pass; the only slot file is docs/luminara_slot.yaml;\n"
    "role, holder, and channel are nested under slots; gamma, lambda, log, and filled_by stay null;\n"
    "the live bind is 0.0.0.0 with PORT default 380; sovereign_automaton_10_06() takes no text;\n"
    "do not overwrite super_symplectic.py with a slot checker; do not print secrets."
)

def _split_kv(line: str):
    in_single = in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == ":" and not in_single and not in_double:
            return line[:i].strip(), line[i + 1:].strip()
    return None

def _strip_inline_comment(value: str) -> str:
    in_single = in_double = False
    for j, ch in enumerate(value):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double and j > 0 and value[j - 1].isspace():
            return value[:j].rstrip()
    return value

def _strip_value(value: str) -> str:
    value = _strip_inline_comment(value).strip()
    if not value:
        return ""
    if len(value) >= 2 and ((value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'")):
        return value[1:-1]
    if value.lower() in ("null", "~"):
        return ""
    return value

def _sanitize_name(name: str) -> str:
    if not name:
        return "_"
    cleaned = "".join(ch if (ch.isalnum() or ch in "_-.") else "_" for ch in name)
    if not cleaned or not (cleaned[0].isalpha() or cleaned[0] == "_"):
        cleaned = "_" + cleaned
    return cleaned

def parse_yaml_to_xml_string(raw_yaml_text: str) -> str:
    root = ET.Element("repository")
    stack = [(-1, root)]
    for raw in raw_yaml_text.splitlines():
        line = raw.rstrip("\r\n")
        if not line.strip() or line.lstrip(" ").startswith("#"):
            continue
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if stripped.startswith("- "):
            item = ET.SubElement(parent, "item")
            item.text = _strip_value(stripped[2:]) or None
            continue
        kv = _split_kv(stripped)
        if kv is None:
            parent.text = ((parent.text or "") + " " + stripped).strip()
            continue
        key, value = kv
        value = _strip_value(value)
        elem = ET.SubElement(parent, _sanitize_name(key))
        elem.text = value or None
        if not value:
            stack.append((indent, elem))
    return ET.tostring(root, encoding="unicode")

def get_security_status(repo_path: str = ".") -> dict:
    print(POLICY_WARNING_TEXT, flush=True)
    status = {
        "policy_warning": POLICY_WARNING_TEXT,
        "canonical_slot_path": CANONICAL_SLOT_FILE,
        "schema_state": "UNKNOWN",
        "listeners_active": False,
        "pyyaml": False,
    }
    target = os.path.join(repo_path, CANONICAL_SLOT_FILE)
    if not os.path.exists(target):
        status["schema_state"] = "PENDING"
        return status
    try:
        raw = open(target, encoding="utf-8").read()
        root = ET.fromstring(parse_yaml_to_xml_string(raw))
    except Exception:
        status["schema_state"] = "FAIL"
        return status
    allowed = {
        "name", "status", "prior_uses_not_definitions", "slots",
        "endpoint_proposed", "live_bind_note", "callable",
        "text_consumed", "filled_by", "commit_identity",
    }
    for child in root:
        if child.tag not in allowed:
            status["schema_state"] = "FAIL"
            return status
    slots = root.find("slots")
    if slots is None:
        status["schema_state"] = "FAIL"
        return status
    role, holder, channel = slots.find("role"), slots.find("holder"), slots.find("channel")
    if role is None or role.text != "chat":
        status["schema_state"] = "FAIL"
        return status
    if holder is None or holder.text != "sovereign_automaton_10.06":
        status["schema_state"] = "FAIL"
        return status
    if channel is None or channel.text != "/mcp/tool":
        status["schema_state"] = "FAIL"
        return status
    for field in ("gamma", "lambda", "log"):
        node = slots.find(field)
        if node is not None and node.text:
            status["schema_state"] = "FAIL"
            return status
    filled = root.find("filled_by")
    if filled is not None and filled.text:
        status["schema_state"] = "FAIL"
        return status
    status["schema_state"] = "PASS"
    return status

if __name__ == "__main__":
    report = get_security_status(sys.argv[2] if len(sys.argv) > 2 else ".")
    print(report["schema_state"])
    if report["schema_state"] == "FAIL":
        sys.exit(1)
    if report["schema_state"] == "PENDING":
        sys.exit(2)
