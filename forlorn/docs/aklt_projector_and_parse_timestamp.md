---
tags:
- s7-s11-lambda0-952072
- "context:952072 nm,952057"
---

# AKLT projector $P_2$ and `parse_timestamp`

## 1. AKLT projector $P_2$

Two spin-1 sites decompose as

$$
3 \otimes 3 = 5 \oplus 3 \oplus 1 \qquad (S = 2,\ 1,\ 0).
$$

Spin-1 matrices in the basis $m = +1, 0, -1$:

$$
S_x = \frac{1}{\sqrt{2}}\begin{pmatrix}0&1&0\\1&0&1\\0&1&0\end{pmatrix},\qquad
S_y = \frac{i}{\sqrt{2}}\begin{pmatrix}0&-1&0\\1&0&-1\\0&1&0\end{pmatrix},\qquad
S_z = \begin{pmatrix}1&0&0\\0&0&0\\0&0&-1\end{pmatrix}.
$$

The two-site dot product is

$$
\mathbf{S}_1\cdot\mathbf{S}_2 = S_x\otimes S_x + S_y\otimes S_y + S_z\otimes S_z .
$$

The projector onto total spin $S = 2$ is

$$
P_2 = \tfrac{1}{6}\left[(\mathbf{S}_1\cdot\mathbf{S}_2)^2 + 3\,\mathbf{S}_1\cdot\mathbf{S}_2 + 2I\right].
$$

The square is of the whole dot product, $(\mathbf{S}_1\cdot\mathbf{S}_2)^2$, not $\mathbf{S}_1\cdot\mathbf{S}_2^2$.

### Eigenvalues

Write $x = \mathbf{S}_1\cdot\mathbf{S}_2$ and $\mathbf{S} = \mathbf{S}_1 + \mathbf{S}_2$. From
$\mathbf{S}^2 = \mathbf{S}_1^2 + \mathbf{S}_2^2 + 2\,\mathbf{S}_1\cdot\mathbf{S}_2$ with
$\mathbf{S}_1^2 = \mathbf{S}_2^2 = s(s+1) = 2$:

$$
x = \tfrac{1}{2}\left(S(S+1) - 4\right).
$$

$x$ is **not** $\mathbf{S}\cdot\mathbf{S}$; it is half of $\mathbf{S}^2$ minus 4. Its eigenvalue on each sector:

| $S$ | multiplicity | $\mathbf{S}^2 = S(S+1)$ | $x$ | $x^2 + 3x + 2$ | $P_2$ |
|---|---|---|---|---|---|
| 2 | 5 | 6 | $+1$ | 6 | 1 |
| 1 | 3 | 2 | $-1$ | 0 | 0 |
| 0 | 1 | 0 | $-2$ | 0 | 0 |

$x^2 + 3x + 2 = (x+1)(x+2)$ vanishes on $S = 1$ and $S = 0$ and equals 6 on $S = 2$, so $P_2$
is the orthogonal projector onto the quintet: $P_2^2 = P_2 = P_2^\dagger$ and
$\operatorname{rank}(P_2) = 5$. Equivalently, $P_2$ is the spectral projector of $\mathbf{S}^2$
for eigenvalue 6.

Checked numerically by `forlorn/docs/test_aklt_projector.py`.

## 2. `parse_timestamp` (`scripts/t_rotator_graphs.py`)

### Input

Raw text. `load_entries` reads each ledger file as text and takes the `timestamp:` value with
`TS_RE = ^timestamp:\s*(.+?)\s*(?:#.*)?$` (multiline, trailing `# comment` dropped). It does
**not** use the YAML-parsed value, so YAML's own date/datetime typing never reaches it.
Surrounding matching `'…'` or `"…"` quotes are removed (`_unquote`) before classification.

### Output

A dict:

```python
{"strict": bool, "kind": str, "iso": str | None, "offset": float | None}
```

`offset` is in **seconds**.

### Kinds

Tried in this order:

| kind | rule | `iso` | `offset` |
|---|---|---|---|
| `strict` | whole string matches `%Y-%m-%dT%H:%M:%SZ` (`STRICT_RE`); `strict = True` | `%Y-%m-%dT%H:%M:%SZ` | seconds from 12:00:00Z on the same UTC day |
| `lenient` | `datetime.fromisoformat` succeeds after `Z → +00:00`, **and** the text contains `T` or a space; a naive value is assumed UTC; converted to UTC | `%Y-%m-%dT%H:%M:%SZ` (UTC) | seconds from 12:00:00Z on the same UTC day |
| `date_only` | a `YYYY-MM-DD` found anywhere in the text (`DATE_RE.search`) | `YYYY-MM-DD` | `None` (no time of day declared) |
| `unparsed` | everything else, including empty or missing input | `None` | `None` |

`strict` is `True` only for kind `strict`.

### Offset $\Phi$

With $t$ the parsed instant, $\mathcal{N}(t)$ its UTC normalisation (naive values taken as UTC) and
$\mathrm{noon}(t)$ = 12:00:00Z on $t$'s UTC day, as (kind, offset in seconds):

$$
\Phi(s)=\begin{cases}
(\texttt{strict},\ t-\mathrm{noon}(t)) & s \text{ matches } \texttt{YYYY-MM-DDTHH:MM:SSZ}\\
(\texttt{lenient},\ \mathcal{N}(t)-\mathrm{noon}(\mathcal{N}(t))) & \texttt{fromisoformat} \text{ parses and } s \text{ has T or a space}\\
(\texttt{date\_only},\ \varnothing) & s \text{ contains } \texttt{YYYY-MM-DD}\\
(\texttt{unparsed},\ \varnothing) & \text{otherwise, or } s \text{ empty}
\end{cases}
$$

$\varnothing$ is `None`: a date-only value never gets a filled-in midnight.

$\Phi \in [-43200, 43200)$: negative before noon, positive after.

### Test cases (`tests/test_t_rotator_graphs.py::test_parse_timestamp_noon_offset`)

| raw | kind | offset (s) | note |
|---|---|---|---|
| `'2026-10-17T03:42:00Z'` | `strict` | $-29880$ ($= -8\cdot3600 - 18\cdot60$) | quotes stripped |
| `"2026-10-16T12:00:00Z"` | `strict` | $0.0$ | exactly noon |
| `2026-10-16T13:00:00+01:00` | `lenient` | $0.0$ | 13:00+01:00 = 12:00Z |
| `ETERNAL_NOW_ANCHORED_TO_2026-09-27Z` | `date_only` | `None` | `iso = 2026-09-27` |
| `PENDING_9283` | `unparsed` | `None` | |

### No idempotency invariant

`parse_timestamp` takes text and returns a dict, so `parse_timestamp(parse_timestamp(x))` is not
defined and there is no idempotency property to state or test. What does hold is that the
`iso` of a `strict` or `lenient` result is itself a `strict` input with the same offset.
