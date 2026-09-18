"""Triune differential — operators called, not plain Fraction identities."""

from terminal_axiom.axiom import Propagation, Root as TRoot, axiom_t0, Location
from producer_axiom.axiom import Generator, Root as PRoot, axiom_p0, Product
from consumer_axiom.axiom import Demand, Supply, axiom_c0, Consumption
from terminal_axiom import certificate as term_cert
from producer_axiom import certificate as prod_cert
from consumer_axiom import certificate as cons_cert


def test_types_distinct():
    t = axiom_t0(Propagation(1.0), TRoot(scale=0.0))
    p = axiom_p0(Generator(1.0), PRoot(scale=1.0))
    c = axiom_c0(Demand(1.0), Supply(0.5))
    assert type(t) is Location
    assert type(p) is Product
    assert type(c) is Consumption


def test_operators_compute_differently():
    assert axiom_t0(Propagation(2.0), TRoot(scale=3.0)).coords[0] == 5.0
    assert axiom_p0(Generator(2.0), PRoot(scale=3.0)).coords[0] == 6.0
    assert axiom_c0(Demand(3.0), Supply(1.0)).amount == 2.0
    assert axiom_c0(Demand(1.0), Supply(5.0)).amount == 0.0


def test_failure_modes_distinct():
    assert axiom_t0(Propagation(5.0), TRoot(scale=0.0)).coords[0] == 5.0
    assert axiom_p0(Generator(5.0), PRoot(scale=0.0)).coords[0] == 0.0
    assert axiom_c0(Demand(1.0), Supply(5.0)).amount == 0.0
    assert axiom_c0(Demand(5.0), Supply(0.0)).amount == 5.0


def test_c0_never_raises_on_zero_root():
    """Saturating C0: R=0 is C=D, not ZeroRootError (that was Spec B division)."""
    c = axiom_c0(Demand(5.0), Supply(0.0))
    assert c.amount == 5.0
    # T0 / P0 also do not raise on zero scale
    assert axiom_t0(Propagation(1.0), TRoot(scale=0.0)).coords[0] == 1.0
    assert axiom_p0(Generator(1.0), PRoot(scale=0.0)).coords[0] == 0.0


def test_oplus_not_same_as_fraction_only_story():
    left_add = axiom_t0(Propagation(6.0), TRoot(scale=9.0)).coords[0]
    assert left_add == 15.0
    residual = axiom_c0(Demand(left_add), Supply(3.0)).amount
    assert residual == 12.0


def test_certificates_three_engines():
    for fn in (term_cert, prod_cert, cons_cert):
        c = fn()
        assert c["all_pass"] is True
        assert c["policy"]["dual_asgi"] == "127.0.0.1:8024"
        assert c["policy"]["mcp_filled"] is False
