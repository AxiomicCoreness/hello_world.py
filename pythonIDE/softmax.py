#!/usr/bin/env python3
"""softmax — numerically stable, temperature-scaled, argparse CLI.

Computes softmax or log-softmax over a vector or matrix.

Input (exactly one of):
    --input '1 2 3'           flat vector from a command-line string
    --input '[[1,2],[3,4]]'   matrix (JSON-like nested brackets)
    --input $'1 2 3\n4 5 6'   matrix via embedded newline
    --file path               read from file (same syntax as --input)
    stdin                     piped input (same syntax as --input)

Output:
    space-separated values, or JSON with --json. Matrix shapes preserved.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

import numpy as np

__all__ = ["softmax", "log_softmax"]


def _stabilize(z: np.ndarray, axis: int) -> np.ndarray:
    """Subtract the max along axis to keep exp in a safe range."""
    return z - np.max(z, axis=axis, keepdims=True)


def log_softmax(
    x: np.ndarray, axis: int = -1, temperature: float = 1.0
) -> np.ndarray:
    """Stable log-softmax: log(softmax(x))."""
    if temperature <= 0:
        raise ValueError("temperature must be > 0")
    z = _stabilize(x / temperature, axis)
    return z - np.log(np.sum(np.exp(z), axis=axis, keepdims=True))


def softmax(
    x: np.ndarray, axis: int = -1, temperature: float = 1.0
) -> np.ndarray:
    """Stable softmax. Subtracts max along axis before exp."""
    if temperature <= 0:
        raise ValueError("temperature must be > 0")
    z = _stabilize(x / temperature, axis)
    e = np.exp(z)
    return e / np.sum(e, axis=axis, keepdims=True)


def parse_array(s: str) -> np.ndarray:
    """Parse a vector or matrix from text.

    Accepts:
        '1 2 3'             -> shape (3,)
        '[1, 2, 3]'         -> shape (3,)
        '[[1,2],[3,4]]'     -> shape (2,2)
        '1 2 3\\n4 5 6'      -> shape (2,3)
    """
    text = s.strip()
    if not text:
        raise ValueError("empty input")

    # Nested brackets: let json do the work.
    if text.startswith("["):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed JSON-like input: {exc.msg}") from None
        arr = np.asarray(data, dtype=float)
        if arr.ndim > 2:
            raise ValueError(f"only vectors and 2-D matrices supported, got rank {arr.ndim}")
        return arr

    # Otherwise: whitespace or comma separated. Multi-line becomes a matrix.
    rows = [line for line in text.splitlines() if line.strip()]
    if len(rows) > 1:
        parsed = [
            [float(tok) for tok in row.replace(",", " ").split()]
            for row in rows
        ]
        widths = {len(r) for r in parsed}
        if len(widths) != 1:
            raise ValueError(f"ragged matrix rows: widths {sorted(widths)}")
        return np.asarray(parsed, dtype=float)

    tokens = rows[0].replace(",", " ").split()
    return np.asarray([float(t) for t in tokens], dtype=float)


def read_input(args: argparse.Namespace) -> np.ndarray:
    """Resolve exactly one input source and parse it."""
    chosen = [
        name for name, val in (
            ("--input", args.input),
            ("--file", args.file),
        ) if val is not None
    ]
    if len(chosen) > 1:
        raise SystemExit(f"specify only one of {chosen}")

    if args.input is not None:
        text = args.input
    elif args.file is not None:
        try:
            text = Path(args.file).read_text(encoding="utf-8")
        except OSError as exc:
            raise SystemExit(f"cannot read {args.file}: {exc.strerror}") from None
    else:
        if sys.stdin.isatty():
            raise SystemExit("no input: pass --input, --file, or pipe stdin")
        text = sys.stdin.read()

    try:
        arr = parse_array(text)
    except ValueError as exc:
        raise SystemExit(f"cannot parse input: {exc}") from None

    if arr.size == 0:
        raise SystemExit("input is empty after parsing")
    return arr


def validate_axis(x: np.ndarray, axis: int) -> None:
    if not (-x.ndim <= axis < x.ndim):
        raise SystemExit(
            f"--axis {axis} out of range for array of rank {x.ndim}"
        )


def format_output(out: np.ndarray, as_json: bool, precision: int) -> str:
    if as_json:
        return json.dumps(out.tolist())
    if out.ndim <= 1:
        return " ".join(f"{v:.{precision}g}" for v in out.ravel())
    return "\n".join(
        " ".join(f"{v:.{precision}g}" for v in row) for row in out
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="softmax",
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--input", "-i", type=str, default=None,
                   help="inline vector or matrix; use --input='-1,2,3' for leading negatives")
    p.add_argument("--file", "-f", type=str, default=None,
                   help="read input from a file")
    p.add_argument("--temperature", "-t", type=float, default=1.0,
                   help="temperature divisor (default: 1.0)")
    p.add_argument("--axis", "-a", type=int, default=-1,
                   help="axis for the reduction (default: -1)")
    p.add_argument("--precision", "-p", type=int, default=6,
                   help="significant digits for non-JSON output (default: 6)")
    p.add_argument("--json", action="store_true",
                   help="emit JSON instead of space-separated values")
    p.add_argument("--log", action="store_true",
                   help="emit log-softmax instead of softmax")
    p.add_argument("--allow-nonfinite", action="store_true",
                   help="permit NaN/inf in the input (default: reject)")
    p.add_argument("--version", action="version", version="softmax 1.1.0")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)

    if args.temperature <= 0:
        p.error("--temperature must be > 0")
    if args.precision < 1:
        p.error("--precision must be >= 1")

    x = read_input(args)
    validate_axis(x, args.axis)

    if not args.allow_nonfinite and not np.all(np.isfinite(x)):
        raise SystemExit(
            "input contains NaN or inf; pass --allow-nonfinite to proceed"
        )

    out = (
        log_softmax(x, axis=args.axis, temperature=args.temperature)
        if args.log
        else softmax(x, axis=args.axis, temperature=args.temperature)
    )

    print(format_output(out, args.json, args.precision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
