from datetime import date, datetime, timedelta

from src.aggregate import build_day_cells, common_basis, totals_by_borough_type
from src.dataset import BOROUGHS, Record


def make_record(borough, ctype, day, hours_to_close=None):
    created = datetime(2025, 1, day, 0, 0, 0)
    closed = None if hours_to_close is None else created + timedelta(hours=hours_to_close)
    return Record(created=created, closed=closed, complaint_type=ctype, agency="AGY",
                  borough=borough, day=date(2025, 1, day))


def test_build_day_cells_counts_open_and_closed():
    records = [
        make_record("BRONX", "NOISE", 1, hours_to_close=None),   # open
        make_record("BRONX", "NOISE", 1, hours_to_close=5),      # closed, within 72h
        make_record("BRONX", "NOISE", 1, hours_to_close=5),      # closed, within 72h
    ]
    day_cells = build_day_cells(records)
    cell = day_cells[date(2025, 1, 1)]["BRONX"]["NOISE"]
    assert cell.n == 3
    assert cell.open_ == 1
    assert cell.closed72 == 2


def test_totals_collapse_across_days():
    records = [
        make_record("BRONX", "NOISE", 1, hours_to_close=5),
        make_record("BRONX", "NOISE", 11, hours_to_close=5),
    ]
    totals = totals_by_borough_type(build_day_cells(records))
    assert totals["BRONX"]["NOISE"].n == 2
    assert totals["BRONX"]["NOISE"].closed72 == 2


def test_common_basis_requires_the_threshold_in_every_borough():
    records = []
    # WIDESPREAD: >=100 in every borough.
    for b in BOROUGHS:
        for i in range(100):
            records.append(make_record(b, "WIDESPREAD", 1, hours_to_close=5))
    # RARE: 100 in four boroughs, only 5 in Staten Island.
    for b in BOROUGHS:
        count = 5 if b == "STATEN ISLAND" else 100
        for i in range(count):
            records.append(make_record(b, "RARE", 1, hours_to_close=5))

    totals = totals_by_borough_type(build_day_cells(records))
    basis = common_basis(totals)

    assert "WIDESPREAD" in basis
    assert "RARE" not in basis


def test_common_basis_empty_when_totals_missing_a_borough():
    # A borough with zero records anywhere: no type can meet the "every borough" bar.
    records = [make_record("BRONX", "NOISE", 1, hours_to_close=5) for _ in range(200)]
    totals = totals_by_borough_type(build_day_cells(records))
    basis = common_basis(totals)
    assert basis == set()
