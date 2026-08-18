#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test surface against live symplectic POD scaffolds (Entry 8536).
"""

import math
import pytest

from celestial.super_simulated_earth import SuperSimulatedEarth, EARTH_FREQUENCY_HZ
from celestial.wasp107b import Wasp107b
from lattice.e8_symplectic import E8Lattice
from cryptography.cmac512 import SovereignCMAC
from prometheus.metrics_server import get_metrics, update_metrics, increment_oracle_query


def test_earth_status_and_coherence():
    earth = SuperSimulatedEarth()
    st = earth.status()
    assert st["resonance_thz"] == 162.28
    assert st["coherence"] == 1.0
    assert st["active"] is True
    assert len(st["anchor_roots"]) == 3


def test_earth_psi4_and_oracle():
    earth = SuperSimulatedEarth()
    psi = earth.psi4(0.0)
    assert abs(psi) > 0
    ans = earth.oracle_query("kepler-452b")
    assert "517.28" in ans
    assert "coherence" in ans


def test_wasp107b_resonance():
    w = Wasp107b()
    st = w.status()
    assert st["mass_mj"] == 0.12
    assert st["period_days"] == 5.72
    assert st["orbital_frequency_hz"] > 0
    assert st["phi_resonance"] > st["orbital_frequency_hz"]


def test_e8_lattice_phase_volume():
    lat = E8Lattice()
    st = lat.status()
    assert st["dimension"] == 248
    assert st["root_count"] == 240
    assert st["coherence_floor"] >= 0.999999
    assert st["phase_volume"] > 0
    assert "Atlas SuperPoD" in st["mapping"]


def test_cmac512_roundtrip():
    mac = SovereignCMAC(b"test-key-phi")
    payload = "ledger/8536.yaml witness"
    tag = mac.mac(payload)
    assert len(tag) == 128  # 64 bytes hex
    assert mac.verify(payload, tag) is True
    assert mac.verify(payload + "x", tag) is False


def test_prometheus_metrics_registry():
    m0 = get_metrics()
    assert "sim_earth_resonance_thz" in m0
    assert m0["sim_earth_resonance_thz"] == 162.28
    update_metrics(gravastar_coherence=0.999)
    increment_oracle_query()
    m1 = get_metrics()
    assert m1["gravastar_coherence"] == 0.999
    assert m1["oracle_query_count"] >= 1.0


def test_earth_frequency_constant():
    assert EARTH_FREQUENCY_HZ == 162.28e12
