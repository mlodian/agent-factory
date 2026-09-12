from pathlib import Path

from src.dataset import load_records
from src.main import analyse, report

FIXTURES = Path(__file__).parent / "fixtures"


def test_report_runs_end_to_end_on_a_small_extract():
    records = load_records(FIXTURES / "mini_311.csv")
    analysis = analyse(records, replicates=20)
    text = report(analysis)

    assert "NYC 311 RESPONSE EQUITY" in text
    assert "POPULATION" in text
    assert "DECOMPOSITION" in text
    assert "COMMON BASIS" in text
    assert "TYPICAL TIME TO CLOSE" in text
    # The population line item and the identity check both assert internally;
    # reaching this point means both passed without raising.
    assert "sum exactly to the population total" in text
    assert "Identity holds for every borough" in text


def test_report_borough_counts_sum_to_total():
    records = load_records(FIXTURES / "mini_311.csv")
    analysis = analyse(records, replicates=10)
    assert sum(analysis.by_borough_count.values()) == len(records)
