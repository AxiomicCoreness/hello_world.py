"""Verified tile set T. Record-level string maps. No seal."""

from __future__ import annotations

Sigma = ("sigma_1", "sigma_2", "sigma_3", "sigma_4", "sigma_5")
FILES_NOTE = "docs/agentic-tilelang-T.yaml"


def apply_tile(i: int, j: int, word: tuple[str, ...]) -> tuple[str, ...]:
    """t_ij appends sigma_{(i*k+j) mod 5 + 1} after each symbol."""
    if not word:
        return ()
    out: list[str] = []
    for k, symbol in enumerate(word):
        appended = Sigma[(i * k + j) % 5]
        out.extend((symbol, appended))
    return tuple(out)


def distinct() -> bool:
    fns = {
        (i, j): tuple((i * k + j) % 5 for k in range(5))
        for i in range(5)
        for j in range(5)
    }
    return len(set(fns.values())) == 25


def length_doubled(word: tuple[str, ...], i: int = 0, j: int = 0) -> bool:
    return len(apply_tile(i, j, word)) == 2 * len(word)
