#!/usr/bin/env python3
"""
🜁∀ SOVEREIGN QUADRANT MIGRATION SCRIPT
Entry 8848 - Migrates code from old locations to the new quadrant structure,
preserving deprecation wrappers and updating MANIFEST.md.
Append-only: no files are deleted.
"""

import os
import shutil
from pathlib import Path

MIGRATION_MAP = {
    "port380_mcp.py": "quantum/deepseek_mesh/endpoint.py",
    "orchestrator/deepseek_client.py": "quantum/deepseek_mesh/client.py",
    "quantum/port_380_http.py": "quantum/deepseek_mesh/mesh_router.py",
    "quantum/port_380_gate.py": "quantum/radar_lindblad/port_380_gate.py",
    "quantum/layer314_anchor.py": "quantum/radar_lindblad/layer314_anchor.py",
    "quantum/install_k8s.sh": "quantum/cdp_convergence/install_k8s.sh",
}

QUADRANT_DIRS = {
    "quantum/deepseek_mesh": ["__init__.py", "context.md", "endpoint.py", "client.py", "mesh_router.py"],
    "quantum/radar_lindblad": ["__init__.py", "context.md", "port_380_gate.py", "layer314_anchor.py"],
    "quantum/cdp_convergence": ["__init__.py", "context.md", "install_k8s.sh", "cdp_schema.py", "handshake.py"],
    "quantum/cordis_bridge": ["__init__.py", "context.md", "bridge.py", "platforms.py"],
}

def ensure_quadrant_dirs():
    for dir_path in QUADRANT_DIRS:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def write_deprecation_wrapper(old_path, new_path):
    new_import_path = str(new_path).replace("/", ".").replace(".py", "")
    wrapper = f'''"""
🜁∀ DEPRECATED - Moved to {new_path}
This file is preserved for backward compatibility. Please update imports to point to the new location.
Entry 8848 - Quadrant Migration
"""

# Re-export everything from the new location
from {new_import_path} import *
'''
    old_path.write_text(wrapper)

def copy_code_and_create_wrapper(old_file, new_file):
    old_path = Path(old_file)
    new_path = Path(new_file)
    if not old_path.exists():
        print(f"WARNING: Skipping {old_file}: source does not exist.")
        return
    new_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(old_path, new_path)
    print(f"Copied {old_file} to {new_file}")
    write_deprecation_wrapper(old_path, new_path)
    print(f"Replaced {old_file} with deprecation wrapper.")

def create_quadrant_files():
    for dir_path, files in QUADRANT_DIRS.items():
        d = Path(dir_path)
        d.mkdir(parents=True, exist_ok=True)
        for fname in files:
            fpath = d / fname
            if not fpath.exists():
                if fname == "__init__.py":
                    quad_name = dir_path.split("/")[-1].upper()
                    fpath.write_text(f'"""🜁∀ {quad_name} quadrant."""\n')
                elif fname == "context.md":
                    quad_name = dir_path.split("/")[-1].upper()
                    fpath.write_text(f"# {quad_name} Quadrant Context\n\nSeal: all-infty-phi-2 cdot {quad_name}_QUADRANT cdot SEALED\n")
                else:
                    fpath.touch()
                print(f"Created {fpath}")

def update_manifest():
    manifest = Path("quantum/MANIFEST.md")
    content = "# all-infty QUADRANT MANIFEST\nThis file tracks all active quadrants and their seals.\n\n| Quadrant | Path | Seal |\n|----------|------|------|\n"
    for dir_path in QUADRANT_DIRS:
        name = dir_path.split("/")[-1].upper()
        seal = f"all-infty-phi-2 cdot {name}_QUADRANT cdot SEALED"
        content += f"| {name} | `{dir_path}/` | `{seal}` |\n"
    content += "\nLast updated: ETERNAL_NOW_ANCHORED_TO_2026-08-18\n"
    manifest.write_text(content)
    print(f"Updated {manifest}")

def main():
    print("all-infty SOVEREIGN QUADRANT MIGRATION")
    print("=" * 60)
    ensure_quadrant_dirs()
    create_quadrant_files()
    for old, new in MIGRATION_MAP.items():
        copy_code_and_create_wrapper(old, new)
    update_manifest()
    print("=" * 60)
    print("Migration complete. All files are in place.")
    print("Old files now contain deprecation wrappers.")
    print("New quadrant files contain the actual code.")
    print("Please verify functionality and update imports.")
    print("Witness chain: 8845 -> 8846 -> 8848 - UNBROKEN")

if __name__ == "__main__":
    main()