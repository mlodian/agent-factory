"""The decomposition's core claim is algebraic: raw_rate - citywide_rate always
equals mix_effect + speed_effect, whatever the data. The Simpson's-paradox fixture
below additionally exercises the reason this project exists: a borough can lead the
raw ranking and trail the standardised one, on the very same underlying speeds.
"""

from src.aggregate import Cell
from src.decompose import collapse_to_basis, decompose


def _identity_holds(decomps, tol=1e-9):
    return all(abs(d.identity_error) < tol for d in decomps)


def test_simpsons_paradox_reverses_the_ranking():
    # BRONX does mostly the easy-to-close type; STATEN ISLAND does mostly the hard
    # one. BRONX is slower than STATEN ISLAND on *both* types individually, but its
    # favourable mix makes its raw rate look better overall -- the textbook paradox.
    collapsed = {
        "BRONX": {"EASY": Cell(n=900, closed72=450), "HARD": Cell(n=100, closed72=5)},
        "STATEN ISLAND": {"EASY": Cell(n=100, closed72=60), "HARD": Cell(n=900, closed72=135)},
        "BROOKLYN": {"EASY": Cell(), "HARD": Cell()},
        "MANHATTAN": {"EASY": Cell(), "HARD": Cell()},
        "QUEENS": {"EASY": Cell(), "HARD": Cell()},
    }

    decomps = decompose(collapsed)
    assert _identity_holds(decomps)

    by_borough = {d.borough: d for d in decomps}
    bronx, staten_island = by_borough["BRONX"], by_borough["STATEN ISLAND"]

    # Bronx is actually slower on every single type...
    assert 450 / 900 < 60 / 100  # EASY: Bronx 50% vs. Staten Island 60%
    assert 5 / 100 < 135 / 900   # HARD: Bronx 5% vs. Staten Island 15%

    # ...yet the raw ranking says the opposite, because of the complaint mix:
    assert bronx.raw_rate > staten_island.raw_rate

    # Standardising onto the shared (citywide) mix reverses it back to the truth:
    assert bronx.standardized_rate < staten_island.standardized_rate


def test_decompose_identity_holds_on_an_asymmetric_five_borough_example():
    collapsed = {
        "BRONX": {"A": Cell(n=300, closed72=200), "B": Cell(n=100, closed72=10), "OTHER": Cell(n=50, closed72=40)},
        "BROOKLYN": {"A": Cell(n=150, closed72=140), "B": Cell(n=300, closed72=100), "OTHER": Cell(n=10, closed72=5)},
        "MANHATTAN": {"A": Cell(n=500, closed72=100), "B": Cell(n=50, closed72=45), "OTHER": Cell(n=5, closed72=1)},
        "QUEENS": {"A": Cell(n=200, closed72=150), "B": Cell(n=200, closed72=120), "OTHER": Cell(n=200, closed72=180)},
        "STATEN ISLAND": {"A": Cell(n=40, closed72=30), "B": Cell(n=40, closed72=5), "OTHER": Cell(n=20, closed72=15)},
    }
    decomps = decompose(collapsed)
    assert _identity_holds(decomps)
    # Sanity: every borough's raw_rate matches closed72/n computed directly.
    for d in decomps:
        cells = collapsed[d.borough].values()
        n, closed = sum(c.n for c in cells), sum(c.closed72 for c in cells)
        assert d.raw_rate == closed / n
        assert d.n == n


def test_collapse_to_basis_folds_rare_types_into_other():
    by_type = {
        "COMMON": Cell(n=500, closed72=400),
        "RARE_1": Cell(n=10, closed72=1),
        "RARE_2": Cell(n=5, closed72=5),
    }
    collapsed = collapse_to_basis(by_type, basis={"COMMON"})
    assert set(collapsed) == {"COMMON", "OTHER"}
    assert collapsed["OTHER"].n == 15
    assert collapsed["OTHER"].closed72 == 6
    assert collapsed["COMMON"].n == 500
