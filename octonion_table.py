"""
Octonion Multiplication Table with Fano Plane Formalism

The octonions are a non-associative, non-commutative algebra over the reals.
They have 8 basis elements: {1, i, j, k, l, il, jl, kl} (or e0-e7).

The Fano plane is a projective plane of order 2 with 7 points and 7 lines.
Each line contains 3 points, and each point is on 3 lines.

For octonions, the Fano plane represents the multiplication relationships:
- The 7 imaginary units {i, j, k, l, il, jl, kl} correspond to the 7 points
- Multiplication of two distinct imaginary units gives a third, following the Fano plane lines
- The sign is determined by the orientation (cyclic order) on the line

Fano plane lines (each line is a triple of basis elements):
1. [i, j, k]     - i*j = k, j*k = i, k*i = j
2. [i, l, il]   - i*l = il, l*il = i, il*i = l
3. [i, jl, kl]  - i*jl = kl, jl*kl = i, kl*i = jl
4. [j, l, kl]   - j*l = kl, l*kl = j, kl*j = l
5. [j, il, jl]  - j*il = jl, il*jl = j, jl*j = il
6. [k, l, jl]   - k*l = jl, l*jl = k, jl*k = l
7. [k, il, kl]  - k*il = kl, il*kl = k, kl*il = i

Sign convention: For a line [a, b, c], we have a*b = c, b*c = a, c*a = b
And the reverse: b*a = -c, c*b = -a, a*c = -b
"""

# Fano plane lines: each line is a cyclic triple
FANO_LINES = [
    [1, 2, 3],   # i, j, k
    [1, 4, 5],   # i, l, il
    [1, 6, 7],   # i, jl, kl
    [2, 4, 7],   # j, l, kl
    [2, 5, 6],   # j, il, jl
    [3, 4, 6],   # k, l, jl
    [3, 5, 7],   # k, il, kl
]

# Basis element names: 0=1, 1=i, 2=j, 3=k, 4=l, 5=il, 6=jl, 7=kl
BASIS_NAMES = ['1', 'i', 'j', 'k', 'l', 'il', 'jl', 'kl']

# Precomputed octonion multiplication table
# table[a][b] = (sign, result_index)
# where sign is +1 or -1, and result_index is the basis element index
_octonion_table = None

def _build_fano_table():
    """Build the octonion multiplication table using Fano plane formalism."""
    global _octonion_table
    if _octonion_table is not None:
        return _octonion_table
    
    size = 8
    table = [[(0, 0) for _ in range(size)] for _ in range(size)]
    
    # Identity: 1 * x = x * 1 = x
    for i in range(size):
        table[0][i] = (1, i)
        table[i][0] = (1, i)
    
    # For each pair of distinct non-identity basis elements (1-7)
    for a in range(1, size):
        for b in range(1, size):
            if a == b:
                # x * x = -1 for imaginary units
                table[a][a] = (-1, 0)
                continue
            
            # Find the line containing both a and b
            found_line = None
            for line in FANO_LINES:
                if a in line and b in line:
                    found_line = line
                    break
            
            if found_line is None:
                # This shouldn't happen for valid Fano plane
                table[a][b] = (0, 0)
                continue
            
            # Find the third element in the line
            c = [x for x in found_line if x != a and x != b][0]
            
            # Determine the sign based on cyclic order
            # For line [x, y, z], we have x*y = z, y*z = x, z*x = y
            # And the reverse: y*x = -z, z*y = -x, x*z = -y
            line = found_line
            idx_a = line.index(a)
            idx_b = line.index(b)
            idx_c = line.index(c)
            
            # Check if (a, b, c) are in cyclic order
            # Cyclic order means idx_b = (idx_a + 1) % 3 and idx_c = (idx_a + 2) % 3
            if (idx_b == (idx_a + 1) % 3) and (idx_c == (idx_a + 2) % 3):
                # a * b = c
                table[a][b] = (1, c)
            elif (idx_a == (idx_b + 1) % 3) and (idx_c == (idx_b + 2) % 3):
                # b * a = c, so a * b = -c
                table[a][b] = (-1, c)
            else:
                # Shouldn't happen
                table[a][b] = (0, 0)
    
    _octonion_table = table
    return table

def build_octonion_table():
    """Build or rebuild the octonion multiplication table."""
    _build_fano_table()
    return _octonion_table

def octonion_product(a, b):
    """
    Compute the product of two octonion basis elements.
    
    Args:
        a: First basis element index (0-7, where 0=1, 1=i, 2=j, 3=k, 4=l, 5=il, 6=jl, 7=kl)
        b: Second basis element index (0-7)
    
    Returns:
        (sign, result_index): sign is +1 or -1, result_index is the basis element index
    """
    table = build_octonion_table()
    if a < 0 or a >= 8 or b < 0 or b >= 8:
        return (0, 0)
    return table[a][b]

def get_basis_name(index):
    """Get the name of a basis element by index."""
    if 0 <= index < len(BASIS_NAMES):
        return BASIS_NAMES[index]
    return f"e{index}"

def verify_fano_properties():
    """Verify that the table satisfies Fano plane properties."""
    table = build_octonion_table()
    
    # Check identity
    for i in range(8):
        assert table[0][i] == (1, i), f"1 * {BASIS_NAMES[i]} != {BASIS_NAMES[i]}"
        assert table[i][0] == (1, i), f"{BASIS_NAMES[i]} * 1 != {BASIS_NAMES[i]}"
    
    # Check squares
    for i in range(1, 8):
        sign, result = table[i][i]
        assert sign == -1 and result == 0, f"{BASIS_NAMES[i]}^2 != -1"
    
    # Check Fano line relationships
    for line in FANO_LINES:
        a, b, c = line
        sign_ab, result_ab = table[a][b]
        sign_bc, result_bc = table[b][c]
        sign_ca, result_ca = table[c][a]
        
        # a * b should equal c (with some sign)
        # b * c should equal a (with some sign)
        # c * a should equal b (with some sign)
        assert result_ab == c, f"{BASIS_NAMES[a]} * {BASIS_NAMES[b]} should give {BASIS_NAMES[c]}, got {BASIS_NAMES[result_ab]}"
        assert result_bc == a, f"{BASIS_NAMES[b]} * {BASIS_NAMES[c]} should give {BASIS_NAMES[a]}, got {BASIS_NAMES[result_bc]}"
        assert result_ca == b, f"{BASIS_NAMES[c]} * {BASIS_NAMES[a]} should give {BASIS_NAMES[b]}, got {BASIS_NAMES[result_ca]}"
    
    return True

# Initialize the table
build_octonion_table()

# Verify properties on module load
verify_fano_properties()