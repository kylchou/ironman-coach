"""Tests for the readiness composite score -- weighting, renormalization
when Garmin data is missing, and the individual component scoring
functions. Pure functions, no DB/Garmin connection needed.
"""
from app.services.readiness import (
    WEIGHTS,
    compute_readiness,
    hrv_score,
    readiness_label,
    rhr_score,
    tsb_score,
)


def test_tsb_score_midpoint_and_bounds():
    assert tsb_score(0) == 50.0
    assert tsb_score(25) == 75.0
    assert tsb_score(100) == 100.0  # clamped
    assert tsb_score(-100) == 0.0  # clamped


def test_hrv_score_known_statuses():
    assert hrv_score("BALANCED") == 100
    assert hrv_score("UNBALANCED") == 55
    assert hrv_score("LOW") == 25
    assert hrv_score("balanced") == 100  # case-insensitive


def test_hrv_score_unknown_status_uses_default():
    assert hrv_score("SOMETHING_NEW_GARMIN_ADDS") == 60


def test_hrv_score_none_is_none():
    assert hrv_score(None) is None


def test_rhr_score_at_baseline_is_100():
    assert rhr_score(50, 50) == 100.0


def test_rhr_score_penalizes_10_points_per_bpm_above_baseline():
    assert rhr_score(53, 50) == 70.0


def test_rhr_score_clamps_at_zero():
    assert rhr_score(70, 50) == 0.0  # 20 bpm above baseline would go negative


def test_rhr_score_missing_data_is_none():
    assert rhr_score(None, 50) is None
    assert rhr_score(50, None) is None


def test_readiness_label_bands():
    assert readiness_label(85) == "Primed"
    assert readiness_label(80) == "Primed"
    assert readiness_label(65) == "Ready"
    assert readiness_label(60) == "Ready"
    assert readiness_label(45) == "Manage fatigue"
    assert readiness_label(40) == "Manage fatigue"
    assert readiness_label(30) == "Recover"


def test_compute_readiness_with_full_data_is_the_weighted_average():
    result = compute_readiness(
        tsb=0,  # -> tsb_score 50
        hrv_status={"status": "BALANCED"},  # -> 100
        sleep={"score": 80, "qualifier": "GOOD"},  # -> 80
        resting_hr=50,
        resting_hr_baseline=50,  # -> rhr_score 100
    )
    expected = (WEIGHTS["tsb"] * 50 + WEIGHTS["hrv"] * 100 + WEIGHTS["sleep"] * 80 + WEIGHTS["rhr"] * 100) / sum(
        WEIGHTS.values()
    )
    assert result.score == round(expected, 1)
    assert result.label == readiness_label(expected)


def test_compute_readiness_renormalizes_around_missing_components():
    # No HRV data at all (common -- needs a fairly recent watch). The score
    # should be the weighted average of just tsb/sleep/rhr, not silently
    # treat the missing HRV as a zero.
    result = compute_readiness(
        tsb=0,  # -> 50
        hrv_status=None,
        sleep={"score": 80, "qualifier": "GOOD"},  # -> 80
        resting_hr=50,
        resting_hr_baseline=50,  # -> 100
    )
    remaining_weight = WEIGHTS["tsb"] + WEIGHTS["sleep"] + WEIGHTS["rhr"]
    expected = (WEIGHTS["tsb"] * 50 + WEIGHTS["sleep"] * 80 + WEIGHTS["rhr"] * 100) / remaining_weight
    assert result.score == round(expected, 1)
    assert result.components["hrv"]["score"] is None


def test_compute_readiness_with_nothing_available_is_neutral_default():
    result = compute_readiness(
        tsb=0,
        hrv_status=None,
        sleep=None,
        resting_hr=None,
        resting_hr_baseline=None,
    )
    # tsb_score(0) is actually available (tsb is always computed, never
    # None), so this only truly hits the "nothing available" branch when
    # tsb itself scores as unavailable -- which it never does. This checks
    # the realistic case instead: everything BUT tsb is missing.
    assert result.components["hrv"]["score"] is None
    assert result.components["sleep"]["score"] is None
    assert result.components["resting_hr"]["score"] is None
    assert result.score == tsb_score(0)


def test_compute_readiness_components_carry_raw_values_for_display():
    result = compute_readiness(
        tsb=5.5,
        hrv_status={"status": "LOW"},
        sleep={"score": 42, "qualifier": "POOR"},
        resting_hr=55,
        resting_hr_baseline=50,
    )
    assert result.components["tsb"]["value"] == 5.5
    assert result.components["hrv"]["status"] == "LOW"
    assert result.components["sleep"]["qualifier"] == "POOR"
    assert result.components["resting_hr"]["value"] == 55
    assert result.components["resting_hr"]["baseline"] == 50
