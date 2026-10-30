# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Master seal string constants for production layout."""

WOOD_DRAGON = "WOOD_DRAGON_0.91"
SEAL_PREFIX = "∀∞φ²"


def seal(tag: str, entry: str | int | None = None) -> str:
    tail = f" · {entry}" if entry is not None else ""
    return f"{SEAL_PREFIX} · {tag}{tail} · {WOOD_DRAGON} · SEALED"
