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

DEFAULT_INTENSITY = 0.6  # assumed for activities with no HR data at all
MAX_INTENSITY = 1.15  # clamp against one-off HR spikes/sensor glitches


def session_load(
    moving_time_s: float | None,
    average_heartrate: float | None,
    max_hr_observed: float | None,
) -> float:
    duration_min = (moving_time_s or 0) / 60
    if duration_min <= 0:
        return 0.0

    if average_heartrate and max_hr_observed:
        intensity = min(average_heartrate / max_hr_observed, MAX_INTENSITY)
    else:
        intensity = DEFAULT_INTENSITY

    return round(duration_min * (intensity**2) * 100, 1)
