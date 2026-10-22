# SPDX-License-Identifier: Apache-2.0
# Derived from vLLM; modified by DeepSeek.

"""Dynamic class loader for agentic workloads.

Supports both:
- Standard .py files
- Macro files that use `from_file "..."` directives to include other macros/classes.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

# Matches: from_file "path/to/macro.inc"  OR  from_file 'path/to/macro.inc'
_FROM_FILE_RE = re.compile(r'^\s*from_file\s+["\']([^"\']+)["\']\s*$', re.MULTILINE)


def _expand_macros(source: str, base_dir: Path, seen: set[Path] | None = None) -> str:
    """
    Recursively expand `from_file "path"` macros by inlining their contents.

    Args:
        source: The macro file text.
        base_dir: Directory to resolve relative `from_file` paths against.
        seen: Set of already-expanded paths (prevents infinite recursion).

    Returns:
        The fully expanded source text with all `from_file` directives replaced.
    """
    if seen is None:
        seen = set()

    def _replace(match: re.Match) -> str:
        rel_path = match.group(1)
        macro_path = (base_dir / rel_path).resolve()

        if macro_path in seen:
            return f"# [load_class] Skipped cyclic from_file: {macro_path}"
        seen.add(macro_path)

        if not macro_path.exists():
            raise FileNotFoundError(f"from_file macro not found: {macro_path}")

        inner_source = macro_path.read_text(encoding="utf-8")
        return _expand_macros(inner_source, macro_path.parent, seen)

    return _FROM_FILE_RE.sub(_replace, source)


def load_class(
    file_path: str | Path,
    class_name: str,
    module_name: str | None = None,
) -> type:
    """
    Dynamically load a .py or macro file and export a specific class from it.

    If the file contains `from_file "..."` directives (macro-style includes),
    they are expanded inline before the module is compiled.

    Args:
        file_path: Path to the .py or macro file.
        class_name: The class to extract.
        module_name: Optional explicit module name. Defaults to the file stem.

    Returns:
        The class object.
    """
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Cannot load class '{class_name}': file not found at {path}")

    raw_source = path.read_text(encoding="utf-8")
    expanded_source = _expand_macros(raw_source, path.parent)

    # Register in sys.modules before exec so dataclasses/pickling work correctly.
    mod_name = module_name or path.stem
    spec = importlib.util.spec_from_loader(mod_name, loader=None)
    module: ModuleType = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module

    try:
        # Compile the fully expanded macro source.
        code = compile(expanded_source, str(path), "exec")
        exec(code, module.__dict__)
    except Exception:
        sys.modules.pop(mod_name, None)
        raise

    if not hasattr(module, class_name):
        raise AttributeError(f"Module '{mod_name}' from {path} does not export '{class_name}'")

    return getattr(module, class_name)
