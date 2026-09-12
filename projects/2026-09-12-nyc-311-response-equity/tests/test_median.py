import math
import statistics

import pytest

from src.median import censored_share, report_median, weighted_median


def _brute_force(pairs):
    expanded = []
    for value, weight in pairs:
        expanded.extend([value] * weight)
    return statistics.median(expanded)


@pytest.mark.parametrize("pairs", [
    [(1.0, 3), (2.0, 1), (3.0, 2)],          # even total weight (6), mixed weights
    [(5.0, 2), (10.0, 2)],                    # even total weight
    [(1.0, 1), (2.0, 1), (3.0, 1)],           # odd count, unit weights
    [(4.0, 1), (4.0, 1), (4.0, 1), (4.0, 1)],  # even count, all identical
])
def test_weighted_median_matches_brute_force_expansion(pairs):
    assert weighted_median(pairs) == _brute_force(pairs)


def test_weighted_median_all_weight_on_one_item():
    assert weighted_median([(7.5, 1), (100.0, 0), (3.0, 50)]) == 3.0
    assert weighted_median([(42.0, 10)]) == 42.0


def test_weighted_median_even_and_odd_total_weight():
    # Even total (10): median is the average of the 5th and 6th expanded values.
    even = [(1.0, 5), (9.0, 5)]
    assert weighted_median(even) == _brute_force(even) == 5.0
    # Odd total (11): median is exactly the 6th expanded value.
    odd = [(1.0, 5), (9.0, 6)]
    assert weighted_median(odd) == _brute_force(odd) == 9.0


def test_weighted_median_raises_on_empty_input():
    with pytest.raises(ValueError):
        weighted_median([])


def test_censored_items_sort_to_the_top_and_can_win_the_median():
    # 6 closed at 5h, 5 censored (open): more than half the weight is finite, so
    # the median is still a real, finite number.
    mostly_closed = [(5.0, 6), (math.inf, 5)]
    assert weighted_median(mostly_closed) == 5.0
    assert censored_share(mostly_closed) == pytest.approx(5 / 11)
    assert report_median(mostly_closed) == "5.0h"

    # Now censored is the majority: the median itself is censored.
    mostly_open = [(5.0, 4), (math.inf, 6)]
    assert math.isinf(weighted_median(mostly_open))
    assert censored_share(mostly_open) == pytest.approx(6 / 10)
    assert report_median(mostly_open) == "> 72 h"


def test_censored_share_of_no_censored_items_is_zero():
    assert censored_share([(1.0, 3), (2.0, 4)]) == 0.0
