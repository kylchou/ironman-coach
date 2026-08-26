"""Per-activity training load estimate, used for the weekly load chart
(Phase 4) and, later, daily fitness/fatigue tracking (Phase 5's CTL/ATL/TSB
model needs a per-day load number to run its rolling averages over -- this
is where that number comes from).

This is deliberately NOT clinical TRIMP: proper TRIMP needs the athlete's
resting HR and a lab-measured (or at least self-reported) max HR, neither
of which we have configured. Instead, intensity is estimated relative to
the highest heart rate observed anywhere in the athlete's own synced
history -- a self-calibrating proxy that needs no configuration -- and
squared to penalize higher intensity more than low, loosely mirroring
TRIMP's exponential weighting. Activities with no HR data fall back to a
fixed moderate-intensity assumption so they still count toward volume.

Revisit this once Phase 5 wants something more rigorous.
"""

from datetime import date, timedelta

DEFAULT_INTENSITY = 0.6  # assumed for activities with no HR data at all
MAX_INTENSITY = 1.15  # clamp against one-off HR spikes/sensor glitches

# Standard Banister impulse-response time constants (days), same ones
# TrainingPeaks' Performance Management Chart uses: CTL ("Fitness") is a
# 42-day exponentially-weighted rolling average of daily load, ATL
# ("Fatigue") is the 7-day version. TSB ("Form") = CTL - ATL.
CTL_DAYS = 42
ATL_DAYS = 7


def session_load(
    moving_time_s: float | None,
    average_heartrate: float | None,
    max_hr_observed: float | None,
) -> float:
    """Loosely modeled on hrTSS: one hour at intensity 1.0 (= max HR ever
    observed) scores exactly 100, matching the conventional TSS scale --
    which matters here because CTL_DAYS/ATL_DAYS and the TSB thresholds
    below (readiness.py's tsb_score too) are the standard ones calibrated
    against that scale. Using minutes instead of hours in this formula
    would inflate everything 60x and silently break both.
    """
    duration_hours = (moving_time_s or 0) / 3600
    if duration_hours <= 0:
        return 0.0

    if average_heartrate and max_hr_observed:
        intensity = min(average_heartrate / max_hr_observed, MAX_INTENSITY)
    else:
        intensity = DEFAULT_INTENSITY

    return round(duration_hours * (intensity**2) * 100, 1)


def daily_loads_from_activities(activities, max_hr_observed: float | None) -> dict[date, float]:
    """Sums session_load per calendar day across a list of Activity rows."""
    totals: dict[date, float] = {}
    for a in activities:
        d = a.start_date.date()
        totals[d] = totals.get(d, 0.0) + session_load(a.moving_time_s, a.average_heartrate, max_hr_observed)
    return totals


def compute_ctl_atl_tsb(daily_loads: dict[date, float], start: date, end: date) -> list[dict]:
    """Runs the CTL/ATL EWMA forward from the earliest available load data
    up through `end`, returning one row per day in [start, end].

    Seeded at 0 rather than backdating -- with ~2 years of real history
    behind any date we'd actually query, both averages are fully converged
    long before `start`, so a zero seed only affects the (unused) warm-up
    period at the very beginning of the athlete's history.
    """
    if not daily_loads:
        first_day = start
    else:
        first_day = min(min(daily_loads), start)

    ctl, atl = 0.0, 0.0
    rows = []
    d = first_day
    while d <= end:
        load = daily_loads.get(d, 0.0)
        ctl += (load - ctl) / CTL_DAYS
        atl += (load - atl) / ATL_DAYS
        if d >= start:
            rows.append({"date": d, "ctl": round(ctl, 1), "atl": round(atl, 1), "tsb": round(ctl - atl, 1)})
        d += timedelta(days=1)
    return rows


def form_label(tsb: float) -> str:
    """Human-readable read on Training Stress Balance -- the same rough
    bands TrainingPeaks/most coaching guides use."""
    if tsb > 10:
        return "Fresh"
    if tsb > -10:
        return "Neutral"
    if tsb > -30:
        return "Fatigued"
    return "Very fatigued"
