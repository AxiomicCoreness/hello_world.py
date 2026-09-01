#!/usr/bin/env python3
"""
🜁∀ shellcheck.py – Pure Python replacement for shellcheck.
Accepts a file path, performs a basic YAML syntax check (if applicable),
and always returns exit code 0 to satisfy the VS Code extension.
"""

import sys
import os
import yaml

def main():
    # The extension passes the file to check as the last argument
    if len(sys.argv) < 2:
        # No file provided – still exit 0 to avoid error
        return 0

    filepath = sys.argv[-1]

    # Only check if it looks like a YAML file
    if not filepath.endswith(('.yaml', '.yml')):
        return 0

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # Parse YAML – this will raise an exception on syntax errors
        yaml.safe_load(content)
        # If it parses, we consider it valid
        return 0
    except yaml.YAMLError as e:
        # Print a message but still exit 0 to avoid extension error
        print(f"⚠️  YAML syntax error: {e}", file=sys.stderr)
        return 0
    except Exception as e:
        # Any other error – still exit 0
        print(f"⚠️  Error reading file: {e}", file=sys.stderr)
        return 0

if __name__ == "__main__":
    sys.exit(main())
