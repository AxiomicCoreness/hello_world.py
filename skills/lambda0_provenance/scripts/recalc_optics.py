#!/usr/bin/env python3
import argparse
import math
import sys

CANONICAL_LAMBDA0_NM = 952072.1
DEPRECATED_LAMBDA0_NM = 952057.0
TOLERANCE_NM = 1.0
# North Star: repo constant NORTH_STAR_HZ / north_star_freq (see SKILL.md Context).
NORTH_STAR_HZ = 71.975
PHASE_LOCK_DEG = 202.6

def calc_lambda0(nkt_sum_nm: float, theta_lock_deg: float) -> float:
    """Calculates lambda0 based on the sum of n_k * t_k and the phase lock."""
    return 360.0 * nkt_sum_nm / theta_lock_deg

def calc_phase_column(nkt_list_nm: list, lambda0_nm: float) -> list:
    """Calculates theta_k for each layer."""
    return [360.0 * nk / lambda0_nm for nk in nkt_list_nm]

def classify_lambda0(lambda0_nm: float) -> str:
    """'deprecated', 'canonical', or 'unrecognised' (within TOLERANCE_NM)."""
    if abs(lambda0_nm - DEPRECATED_LAMBDA0_NM) < TOLERANCE_NM:
        return "deprecated"
    if abs(lambda0_nm - CANONICAL_LAMBDA0_NM) < TOLERANCE_NM:
        return "canonical"
    return "unrecognised"

def check_north_star(hz: float) -> bool:
    """True when hz equals the repo North Star 71.975 Hz (to 1e-9 Hz)."""
    return math.isfinite(hz) and abs(hz - NORTH_STAR_HZ) < 1e-9

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Verify optical layer stack phase drift.")
    parser.add_argument("--nkt-sum", type=float, default=535805.0, help="Sum of n_k * t_k in nm")
    parser.add_argument("--theta-lock", type=float, default=202.60, help="Target phase lock in degrees")
    parser.add_argument("--north-star", type=float, nargs="?", const=NORTH_STAR_HZ, default=None,
                        metavar="HZ", help="Echo and validate the North Star frequency (default 71.975 Hz)")
    args = parser.parse_args(argv)

    lambda0 = calc_lambda0(args.nkt_sum, args.theta_lock)
    f0_ghz = 299792458 / (lambda0 * 1e-9) / 1e9

    print(f"[*] Inputs: Σnₖtₖ = {args.nkt_sum} nm, θ_lock = {args.theta_lock}°")
    print(f"[*] Derived λ₀: {lambda0:.2f} nm")
    print(f"[*] Derived f₀: {f0_ghz:.2f} GHz")

    verdict = classify_lambda0(lambda0)
    if verdict == "deprecated":
        print("[!] WARNING: Using deprecated 952,057 nm draft.")
    elif verdict == "canonical":
        print("[+] OK: Matches canonical 952,072.1 nm.")
    else:
        print(f"[?] UNRECOGNISED: λ₀ = {lambda0:.2f} nm matches neither canonical "
              f"952,072.1 nm nor deprecated 952,057 nm (±{TOLERANCE_NM:g} nm).")

    rc = 0
    if args.north_star is not None:
        if check_north_star(args.north_star):
            print(f"[+] North Star: {args.north_star:g} Hz matches {NORTH_STAR_HZ} Hz "
                  f"(phase lock {PHASE_LOCK_DEG}°).")
        else:
            print(f"[!] North Star: {args.north_star:g} Hz != {NORTH_STAR_HZ} Hz.")
            rc = 1
    return rc

if __name__ == "__main__":
    sys.exit(main())
