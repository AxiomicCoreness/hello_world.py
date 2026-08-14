#!/usr/bin/env python3
"""Tokenizer binary wire format — struct '>q' (signed 64-bit BE, 8 bytes)."""
from __future__ import annotations

import struct
from typing import Iterable, List

FMT = ">q"
TOKEN_BYTES = struct.calcsize(FMT)  # 8


def pack_token(value: int) -> bytes:
    """Pack one signed integer token as 8-byte big-endian."""
    return struct.pack(FMT, int(value))


def unpack_token(data: bytes) -> int:
    if len(data) != TOKEN_BYTES:
        raise ValueError(f"expected {TOKEN_BYTES} bytes, got {len(data)}")
    return struct.unpack(FMT, data)[0]


def pack_tokens(values: Iterable[int]) -> bytes:
    return b"".join(pack_token(v) for v in values)


def unpack_tokens(data: bytes) -> List[int]:
    if len(data) % TOKEN_BYTES:
        raise ValueError("buffer length not multiple of 8")
    return [struct.unpack_from(FMT, data, i)[0] for i in range(0, len(data), TOKEN_BYTES)]


if __name__ == "__main__":
    assert TOKEN_BYTES == 8
    raw = pack_token(0x123456789)
    assert unpack_token(raw) == 0x123456789
    print(f"FMT={FMT!r} TOKEN_BYTES={TOKEN_BYTES} OK")
