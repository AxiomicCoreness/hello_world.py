# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""``python -m sovereign`` — stdlib dispatcher for the sovereign package.

Subcommands import their modules only when invoked. ``paper`` delegates to
``paper_mcp.cli.main`` and exits 1 when that package is not importable.
"""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Sequence


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sovereign",
        description="Sovereign package commands. Imports stay lazy.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    engine = sub.add_parser("engine", help="Engine body (scripts/ml_sovereign_core.py).")
    engine_sub = engine.add_subparsers(dest="engine_cmd", required=True)
    engine_sub.add_parser("phi", help="Print PHI and the seed-polynomial residual.")

    kernel = sub.add_parser("kernel", help="Adjudication kernel (wired_kernel).")
    kernel_sub = kernel.add_subparsers(dest="kernel_cmd", required=True)
    kernel_sub.add_parser(
        "self-test",
        help="Catch a fabricated PHI power and a bad digest shape.",
    )

    octonion = sub.add_parser(
        "octonion_table",
        help="Fano-plane octonion table.",
    )
    oct_sub = octonion.add_subparsers(dest="octonion_cmd", required=True)
    oct_sub.add_parser("verify", help="Run verify_fano_properties().")
    product = oct_sub.add_parser("product", help="Print sign and basis index.")
    product.add_argument("a", type=int)
    product.add_argument("b", type=int)

    phi = sub.add_parser("phi_mod_mean", help="scripts/phi_mod_mean.py re-export.")
    phi_sub = phi.add_subparsers(dest="phi_cmd", required=True)
    phi_sub.add_parser(
        "phi",
        help="Print PHI and |PHI^2 - PHI - 1|. Does not run the mod-mean gate.",
    )

    aklt = sub.add_parser("aklt_e2e", help="aklt_invariants re-export.")
    aklt_sub = aklt.add_subparsers(dest="aklt_cmd", required=True)
    aklt_sub.add_parser("names", help="List the re-exported public names.")

    paper = sub.add_parser(
        "paper",
        help="Delegate remaining arguments to paper_mcp.cli.",
    )
    paper.add_argument("paper_args", nargs=argparse.REMAINDER)
    return parser


def _cmd_engine_phi() -> int:
    import sovereign.engine as engine

    phi = float(engine.PHI)
    residual = abs((phi * phi) - phi - 1.0)
    sys.stdout.write("PHI={0:.15f}\n".format(phi))
    sys.stdout.write("residual={0:.3e}\n".format(residual))
    return 0 if residual < 1e-9 else 1


def _cmd_kernel_self_test() -> int:
    from sovereign.kernel import adjudicate

    record = adjudicate(
        "kernel self-test: PHI34 = 2123456.0",
        numbers={"PHI34": 2123456.0},
        hex_digests=["8F1A3D9C04B27E5E"],
    )
    gates = record["gates"]
    ok = (
        gates[0][1] == "FALSE"
        and gates[1][1] == "FALSE"
        and record["verdict"] == "FALSE"
    )
    sys.stdout.write("verdict={0}\n".format(record["verdict"]))
    return 0 if ok else 1


def _cmd_octonion_verify() -> int:
    from sovereign.octonion_table import verify_fano_properties

    verify_fano_properties()
    sys.stdout.write("fano=ok\n")
    return 0


def _cmd_octonion_product(a: int, b: int) -> int:
    from sovereign.octonion_table import octonion_product

    sign, index = octonion_product(a, b)
    sys.stdout.write("{0} {1}\n".format(sign, index))
    return 0


def _cmd_phi() -> int:
    from sovereign.phi_mod_mean import PHI

    residual = abs((PHI * PHI) - PHI - 1.0)
    sys.stdout.write("PHI={0:.15f}\n".format(PHI))
    sys.stdout.write("residual={0:.3e}\n".format(residual))
    return 0 if residual < 1e-12 else 1


def _cmd_aklt_names() -> int:
    import sovereign.aklt_e2e as aklt

    for name in sorted(aklt.__all__):
        sys.stdout.write(name + "\n")
    return 0


def _cmd_paper(paper_args: Sequence[str]) -> int:
    argv: List[str] = list(paper_args)
    if argv and argv[0] == "--":
        argv = argv[1:]
    try:
        from paper_mcp.cli import main as paper_main
    except ImportError:
        sys.stderr.write(
            "paper_mcp is not importable on this checkout\n"
        )
        return 1
    code = paper_main(argv)
    if code is None:
        return 0
    return int(code)


def main(argv: Optional[Sequence[str]] = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    # paper_mcp flags such as --root must not be parsed by this dispatcher.
    if raw and raw[0] == "paper":
        return _cmd_paper(raw[1:])
    parser = _parser()
    args = parser.parse_args(raw)
    if args.command == "engine":
        return _cmd_engine_phi()
    if args.command == "kernel":
        return _cmd_kernel_self_test()
    if args.command == "octonion_table" and args.octonion_cmd == "verify":
        return _cmd_octonion_verify()
    if args.command == "octonion_table" and args.octonion_cmd == "product":
        return _cmd_octonion_product(args.a, args.b)
    if args.command == "phi_mod_mean":
        return _cmd_phi()
    if args.command == "aklt_e2e":
        return _cmd_aklt_names()
    if args.command == "paper":
        return _cmd_paper(args.paper_args)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
