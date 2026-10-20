# tests/test_octonion_table.py
import itertools
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lattice import octonion_table as ot  # noqa: E402

B = range(8)
IM = range(1, 8)


def basis(i):
    v = [0.0] * 8
    v[i] = 1.0
    return v


def close(a, b, tol=1e-9):
    return all(abs(x - y) < tol for x, y in zip(a, b))


def rand_oct(rng):
    return [rng.uniform(-1, 1) for _ in range(8)]


def test_table_is_full_signed_permutation():
    assert len(ot.OCTONION_MUL) == 64
    for i in B:
        row = [ot.octonion_mul(i, j)[0] for j in B]
        assert sorted(row) == list(B)
        assert all(ot.octonion_mul(i, j)[1] in (1, -1) for j in B)


def test_triples_match_declared_orientation():
    for a, b, c in ot.FANO_TRIPLES:
        for x, y, z in ((a, b, c), (b, c, a), (c, a, b)):
            assert ot.octonion_mul(x, y) == (z, 1)
            assert ot.octonion_mul(y, x) == (z, -1)


def test_identity_and_squares():
    for i in B:
        assert ot.octonion_mul(0, i) == (i, 1)
        assert ot.octonion_mul(i, 0) == (i, 1)
    for i in IM:
        assert ot.octonion_mul(i, i) == (0, -1)


def test_anticommutation():
    for i, j in itertools.permutations(IM, 2):
        k1, s1 = ot.octonion_mul(i, j)
        k2, s2 = ot.octonion_mul(j, i)
        assert k1 == k2 and s1 == -s2


def test_alternativity_on_basis():
    for i, j in itertools.product(B, B):
        x, y = basis(i), basis(j)
        assert close(ot.mul(x, ot.mul(x, y)), ot.mul(ot.mul(x, x), y))
        assert close(ot.mul(ot.mul(y, x), x), ot.mul(y, ot.mul(x, x)))


def test_alternativity_moufang_norm_on_random():
    rng = random.Random(9280)
    for _ in range(200):
        x, y, z = rand_oct(rng), rand_oct(rng), rand_oct(rng)
        m = ot.mul
        assert close(m(x, m(x, y)), m(m(x, x), y))
        assert close(m(m(y, x), x), m(y, m(x, x)))
        assert close(m(z, m(x, m(z, y))), m(m(m(z, x), z), y))      # left Moufang
        assert close(m(x, m(z, m(y, z))), m(m(m(x, z), y), z))      # right Moufang
        assert close(m(m(z, x), m(y, z)), m(m(z, m(x, y)), z))      # middle Moufang
        assert abs(ot.norm(m(x, y)) - ot.norm(x) * ot.norm(y)) < 1e-9


def test_non_associative():
    assert ot.basis_mul3_left(1, 2, 4) == (7, 1)
    assert ot.basis_mul3_right(1, 2, 4) == (7, -1)
    bad = sum(ot.basis_mul3_left(i, j, k) != ot.basis_mul3_right(i, j, k)
              for i, j, k in itertools.product(IM, repeat=3))
    assert bad == 168


def test_conjugate_and_norm():
    assert ot.octonion_conjugate(0) == (0, 1)
    for i in IM:
        assert ot.octonion_conjugate(i) == (i, -1)
        # e_i * conj(e_i) = +1
        k, s = ot.octonion_conjugate(i)
        kk, ss = ot.octonion_mul(i, k)
        assert (kk, s * ss) == (0, 1)
    assert all(ot.octonion_norm(i) == 1 for i in B)
    with pytest.raises(ValueError):
        ot.octonion_conjugate(8)
    rng = random.Random(1)
    x = rand_oct(rng)
    xc = ot.mul(x, ot.conj(x))
    assert abs(xc[0] - ot.norm(x) ** 2) < 1e-12 and all(abs(v) < 1e-12 for v in xc[1:])


def test_flipped_orientation_is_not_octonions():
    flipped = [(1, 2, 3), (1, 4, 5), (1, 6, 7), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 5, 6)]
    t = ot.build_table(flipped)

    def m(x, y):
        out = [0.0] * 8
        for i in B:
            for j in B:
                k, s = t[(i, j)]
                out[k] += s * x[i] * y[j]
        return out

    rng = random.Random(0)
    x, y = rand_oct(rng), rand_oct(rng)
    assert not close(m(x, m(x, y)), m(m(x, x), y))
    assert abs(ot.norm(m(x, y)) - ot.norm(x) * ot.norm(y)) > 1e-6
