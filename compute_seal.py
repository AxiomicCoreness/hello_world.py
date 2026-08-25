#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_seal.py – Compute SHA3-256 seals for ledger entries.

Usage:
    python3 compute_seal.py < ledger_aggregate.yaml > ledger_sealed.yaml
    
    # Or process a single entry file
    python3 compute_seal.py ledger/0351.yaml
    
    # Or process all entries in ledger directory
    for f in ledger/*.yaml; do
        python3 compute_seal.py "$f" > "$f.tmp" && mv "$f.tmp" "$f"
    done

Seal: ∀∞φ² · COMPUTE_SEAL · WOOD_DRAGON_MOUNTS_OFFENSE · SEALED
"""

import sys
import json
import hashlib
import yaml
from pathlib import Path


def compute_seal(entry: dict) -> str:
    """
    Compute SHA3-256 hash of entry for seal.
    Excludes the 'seal' field itself to avoid circular dependency.
    """
    data = {k: v for k, v in entry.items() if k != 'seal'}
    canon = json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha3_256(canon.encode('utf-8')).hexdigest()


def compute_witness_prefix(entry_index: int) -> str:
    """
    Compute deterministic witness prefix from entry index.
    Returns first 16 characters of SHA3-256 hash.
    """
    return hashlib.sha3_256(f"{entry_index:04d}".encode('utf-8')).hexdigest()[:16]


def fix_entry(entry: dict) -> dict:
    """
    Fix a single ledger entry:
    - Replace <hash_here> in seal with actual SHA3-256
    - Replace <sha3-256> in witness_prefix with computed hash
    """
    if not isinstance(entry, dict):
        return entry
    
    seal_hash = compute_seal(entry)
    
    if 'seal' in entry and isinstance(entry['seal'], str):
        entry['seal'] = entry['seal'].replace('<hash_here>', seal_hash)
    
    idx = entry.get('entry_index')
    if idx is not None:
        if 'witness_prefix' in entry:
            if entry['witness_prefix'] in ('<sha3-256>', None, '', 'None'):
                entry['witness_prefix'] = compute_witness_prefix(int(idx))
        else:
            entry['witness_prefix'] = compute_witness_prefix(int(idx))
    
    return entry


def process_stream():
    """Process YAML from stdin, output to stdout."""
    docs = yaml.safe_load_all(sys.stdin)
    first = True
    for doc in docs:
        if doc is None:
            continue
        fixed = fix_entry(doc)
        if not first:
            print('---')
        yaml.dump(fixed, sys.stdout, sort_keys=False, default_flow_style=False, allow_unicode=True)
        first = False


def process_file(filepath: str):
    """Process a single YAML file, overwrite in place."""
    path = Path(filepath)
    if not path.exists():
        print(f"❌ File not found: {filepath}", file=sys.stderr)
        return
    
    with path.open('r', encoding='utf-8') as f:
        docs = list(yaml.safe_load_all(f))
    
    fixed_docs = [fix_entry(doc) if isinstance(doc, dict) else doc for doc in docs]
    
    with path.open('w', encoding='utf-8') as f:
        yaml.dump_all(fixed_docs, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ Fixed: {filepath}")


def process_directory(directory: str):
    """Process all YAML files in a directory."""
    dir_path = Path(directory)
    if not dir_path.is_dir():
        print(f"❌ Directory not found: {directory}", file=sys.stderr)
        return
    
    for yaml_file in dir_path.glob('*.yaml') + dir_path.glob('*.yml'):
        process_file(str(yaml_file))


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        process_stream()
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
        if Path(arg).is_dir():
            process_directory(arg)
        else:
            process_file(arg)
    else:
        for arg in sys.argv[1:]:
            process_file(arg)


if __name__ == "__main__":
    main()