"""Tests for the training-load math -- session_load in particular, since a
units bug here (minutes instead of hours) once inflated every number 60x and
silently saturated the readiness score. Pure functions, no DB needed.
"""
from datetime import date, datetime, timedelta, timezone

from app.services.training_load import (
    ATL_DAYS,
    CTL_DAYS,
    compute_ctl_atl_tsb,
    daily_loads_from_activities,
    form_label,
    session_load,
)


class FakeActivity:
    def __init__(self, start_date, moving_time_s, average_heartrate=None):
        self.start_date = start_date
        self.moving_time_s = moving_time_s
        self.average_heartrate = average_heartrate


def test_session_load_zero_with_no_duration():
    assert session_load(None, 150, 190) == 0.0
    assert session_load(0, 150, 190) == 0.0


def test_session_load_one_hour_at_max_hr_scores_100():
    # This is the pinned regression case for the minutes-vs-hours bug: one
    # hour at exactly max observed HR should score exactly 100, matching
    # the conventional TSS scale. It was scoring ~6000 before the fix.
    assert session_load(moving_time_s=3600, average_heartrate=190, max_hr_observed=190) == 100.0


def test_session_load_scales_with_duration():
    half_hour = session_load(1800, 190, 190)
    one_hour = session_load(3600, 190, 190)
    assert half_hour == one_hour / 2


def test_session_load_intensity_is_squared():
    # 50% of max HR should score 25% of the full-intensity load (0.5^2), not 50%.
    half_intensity = session_load(3600, 95, 190)
    assert half_intensity == 25.0


def test_session_load_clamps_intensity_spikes():
    # average > max shouldn't happen in real data, but a sensor glitch could
    # produce it -- should clamp rather than blow past MAX_INTENSITY.
    clamped = session_load(3600, 300, 190)
    uncapped_equivalent = session_load(3600, 190 * 1.15, 190)
    assert clamped == uncapped_equivalent


def test_session_load_falls_back_to_default_intensity_without_hr():
    result = session_load(3600, None, 190)
    assert result == round(0.6**2 * 100, 1)


def test_daily_loads_sums_multiple_activities_same_day():
    day = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    same_day_later = datetime(2026, 1, 1, 18, 0, tzinfo=timezone.utc)
    other_day = datetime(2026, 1, 2, 8, 0, tzinfo=timezone.utc)
    activities = [
        FakeActivity(day, 3600, 190),
        FakeActivity(same_day_later, 3600, 190),
        FakeActivity(other_day, 3600, 190),
    ]

    totals = daily_loads_from_activities(activities, max_hr_observed=190)
    assert totals[date(2026, 1, 1)] == 200.0
    assert totals[date(2026, 1, 2)] == 100.0


def test_compute_ctl_atl_tsb_converges_under_steady_load():
    # A constant daily load, run for many multiples of CTL_DAYS, should
    # converge CTL and ATL to (almost) that load, putting TSB near zero.
    start = date(2026, 1, 1)
    end = start
    daily_loads = {}
    d = date(2025, 1, 1)  # a full year of runway, well past CTL_DAYS/ATL_DAYS to converge in
    while d <= start:
        daily_loads[d] = 50.0
        d += timedelta(days=1)

    rows = compute_ctl_atl_tsb(daily_loads, start, end)
    assert len(rows) == 1
    row = rows[0]
    assert abs(row["ctl"] - 50.0) < 1.0
    assert abs(row["atl"] - 50.0) < 1.0
    assert abs(row["tsb"]) < 1.0


def test_compute_ctl_atl_tsb_only_returns_requested_range():
    daily_loads = {date(2026, 1, 1): 100.0, date(2026, 1, 5): 100.0}
    start = date(2026, 1, 3)
    end = date(2026, 1, 5)
    rows = compute_ctl_atl_tsb(daily_loads, start, end)
    assert [r["date"] for r in rows] == [date(2026, 1, 3), date(2026, 1, 4), date(2026, 1, 5)]


def test_compute_ctl_atl_tsb_rises_after_a_hard_day():
    # Rested (zero load) for a while, then one big day -- ATL (7-day, fast)
    # should jump more than CTL (42-day, slow) does, since that's the whole
    # point of the two different time constants.
    start = date(2026, 2, 1)
    daily_loads = {date(2026, 1, 1): 0.0, start: 100.0}
    rows = compute_ctl_atl_tsb(daily_loads, start, start)
    row = rows[0]
    assert row["atl"] > row["ctl"]
    assert row["atl"] == round(100.0 / ATL_DAYS, 1)
    assert row["ctl"] == round(100.0 / CTL_DAYS, 1)


def test_form_label_bands():
    assert form_label(15) == "Fresh"
    assert form_label(0) == "Neutral"
    assert form_label(-20) == "Fatigued"
    assert form_label(-40) == "Very fatigued"
    # Boundaries themselves belong to the band below, not above.
    assert form_label(10) == "Neutral"
    assert form_label(-10) == "Fatigued"
    assert form_label(-30) == "Very fatigued"
