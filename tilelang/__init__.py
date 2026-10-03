"""tilelang — string tile set plus declared additives.

T is the affine rewrite in docs/agentic-tilelang-T.yaml.
Phase tiles and the Eridanus field are not elements of T.
"""

from tilelang.tiles import FILES_NOTE, Sigma, apply_tile, distinct

__all__ = ["Sigma", "apply_tile", "distinct", "FILES_NOTE"]
