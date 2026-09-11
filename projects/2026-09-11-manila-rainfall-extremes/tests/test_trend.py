"""Mann-Kendall and Theil-Sen, checked against series whose answer is known.

The fixtures here are constructed by hand on purpose — a trend test must be
verified against inputs whose correct output is known in advance, which real
rainfall never is. This is the one directory where invented numbers are correct.
"""

from __future__ import annotations

import math

import pytest

from src.trend import ALPHA, analyse, mann_kendall_s, theil_sen

YEARS = [float(y) for y in range(2000, 2030)]  # 30 points


def test_s_counts_concordant_pairs():
    # Every later value exceeds every earlier one: all C(4,2) = 6 pairs concordant.
    assert mann_kendall_s([1.0, 2.0, 3.0, 4.0]) == 6
    assert mann_kendall_s([4.0, 3.0, 2.0, 1.0]) == -6
    assert mann_kendall_s([7.0, 7.0, 7.0, 7.0]) == 0


def test_strictly_increasing_series_is_detected():
    values = [float(i) for i in range(len(YEARS))]
    result = analyse(YEARS, values)

    assert result.significant
    assert result.direction == "rising"
    assert result.tau == pytest.approx(1.0)
    assert result.p_value < 1e-6
    # One unit per year, by construction.
    assert result.slope_per_year == pytest.approx(1.0)
    assert result.slope_per_decade == pytest.approx(10.0)


def test_strictly_decreasing_series_is_detected():
    values = [float(-i) for i in range(len(YEARS))]
    result = analyse(YEARS, values)

    assert result.significant
    assert result.direction == "falling"
    assert result.tau == pytest.approx(-1.0)
    assert result.slope_per_decade == pytest.approx(-10.0)


def test_flat_series_shows_no_trend():
    result = analyse(YEARS, [5.0] * len(YEARS))

    assert not result.significant
    assert result.direction == "no detectable trend"
    assert result.s == 0
    assert result.z == 0.0
    assert result.p_value == pytest.approx(1.0)
    assert result.slope_per_decade == pytest.approx(0.0)


def test_alternating_series_shows_no_trend():
    """A sawtooth has large swings but no monotonic drift — must not fire."""
    values = [10.0 if i % 2 else 0.0 for i in range(len(YEARS))]
    result = analyse(YEARS, values)

    assert not result.significant
    assert result.p_value > ALPHA


def test_one_outlier_does_not_swing_theil_sen():
    """The reason for using Theil-Sen over least squares, stated as a test."""
    flat = [10.0] * len(YEARS)
    spiked = list(flat)
    spiked[-1] = 10_000.0  # a freak typhoon year

    slope, _ = theil_sen(YEARS, spiked)
    assert slope == pytest.approx(0.0)

    # Least squares on the same input is dragged well off zero.
    n = len(YEARS)
    mean_t = sum(YEARS) / n
    mean_v = sum(spiked) / n
    ols = sum((t - mean_t) * (v - mean_v) for t, v in zip(YEARS, spiked)) / sum(
        (t - mean_t) ** 2 for t in YEARS
    )
    assert ols > 10.0


def test_theil_sen_recovers_an_exact_line():
    values = [3.0 * t - 5990.0 for t in YEARS]
    slope, intercept = theil_sen(YEARS, values)

    assert slope == pytest.approx(3.0)
    for t, v in zip(YEARS, values):
        assert slope * t + intercept == pytest.approx(v)


def test_ties_reduce_variance_and_p_stays_valid():
    """Heavy ties are the normal case for integer day-counts; p must stay in [0,1]."""
    values = [0.0] * 15 + [1.0] * 15
    result = analyse(YEARS, values)

    assert 0.0 <= result.p_value <= 1.0
    assert result.s > 0


def test_verdict_reports_the_units_it_was_given():
    result = analyse(YEARS, [float(i) for i in range(len(YEARS))])

    assert "days/decade" in result.verdict("days")
    assert "mm/decade" in result.verdict("mm")


def test_short_series_is_refused_not_guessed():
    """Below n=10 the normal approximation is optimistic — better to refuse."""
    with pytest.raises(ValueError, match="at least 10 points"):
        analyse(YEARS[:5], [1.0, 2.0, 3.0, 4.0, 5.0])


def test_length_mismatch_is_refused():
    with pytest.raises(ValueError, match="length mismatch"):
        analyse(YEARS, [1.0, 2.0])


def test_p_value_matches_the_normal_tail():
    """erfc(|z|/sqrt 2) must equal the two-sided normal p it stands in for."""
    values = [float(i) for i in range(len(YEARS))]
    result = analyse(YEARS, values)
    expected = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(result.z) / math.sqrt(2.0))))

    assert result.p_value == pytest.approx(expected, abs=1e-12)
