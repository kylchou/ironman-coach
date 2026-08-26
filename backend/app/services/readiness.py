"""Composite daily readiness score: a heuristic blend of Training Stress
Balance (from our own synced activity history) with real physiological
recovery signals from Garmin -- HRV status, sleep score, and resting HR vs
personal baseline. Not a clinical or medically-validated score.

Any component Garmin has no data for on a given day (device-dependent --
HRV in particular needs a fairly recent watch) is simply left out and the
remaining weights renormalized, rather than failing outright or, worse,
silently treating "no data" as "bad".

The weights below are a reasonable starting point, not derived from any
study. Worth tuning once you have a felt sense of whether the score
actually tracks how recovered you feel day to day.
"""

from dataclasses import dataclass, field

WEIGHTS = {"tsb": 35, "hrv": 30, "sleep": 25, "rhr": 10}
RHR_BASELINE_DAYS = 30  # must match garmin_client.fetch_resting_hr_baseline's default

HRV_STATUS_SCORES = {"BALANCED": 100, "UNBALANCED": 55, "LOW": 25}
HRV_STATUS_DEFAULT = 60  # an HRV status Garmin reports that isn't in the map above


def tsb_score(tsb: float) -> float:
    """TSB 0 -> 50 ("neutral"); +25 -> 100 ("very fresh"); -50 -> 0 ("very fatigued")."""
    return max(0.0, min(100.0, 50 + tsb))


def hrv_score(status: str | None) -> float | None:
    if not status:
        return None
    return HRV_STATUS_SCORES.get(status.upper(), HRV_STATUS_DEFAULT)


def rhr_score(today_rhr: float | None, baseline_rhr: float | None) -> float | None:
    if today_rhr is None or baseline_rhr is None:
        return None
    delta = today_rhr - baseline_rhr
    return max(0.0, min(100.0, 100 - delta * 10))  # -10 pts per bpm above baseline


def readiness_label(score: float) -> str:
    if score >= 80:
        return "Primed"
    if score >= 60:
        return "Ready"
    if score >= 40:
        return "Manage fatigue"
    return "Recover"


@dataclass
class ReadinessResult:
    score: float
    label: str
    components: dict = field(default_factory=dict)


def compute_readiness(
    tsb: float,
    hrv_status: dict | None,
    sleep: dict | None,
    resting_hr: float | None,
    resting_hr_baseline: float | None,
) -> ReadinessResult:
    scores = {
        "tsb": tsb_score(tsb),
        "hrv": hrv_score(hrv_status["status"] if hrv_status else None),
        "sleep": sleep["score"] if sleep else None,
        "rhr": rhr_score(resting_hr, resting_hr_baseline),
    }

    available = {k: v for k, v in scores.items() if v is not None}
    if available:
        total_weight = sum(WEIGHTS[k] for k in available)
        composite = sum(WEIGHTS[k] * v for k, v in available.items()) / total_weight
    else:
        composite = 50.0  # nothing to go on -- neutral default, not a false "fine" or "bad"

    return ReadinessResult(
        score=round(composite, 1),
        label=readiness_label(composite),
        components={
            "tsb": {"value": tsb, "score": scores["tsb"]},
            "hrv": {"status": hrv_status["status"] if hrv_status else None, "score": scores["hrv"]},
            "sleep": {
                **(sleep or {}),
                "value": sleep["score"] if sleep else None,
                "qualifier": sleep["qualifier"] if sleep else None,
                "score": scores["sleep"],
            },
            "resting_hr": {
                "value": resting_hr,
                "baseline": resting_hr_baseline,
                "baseline_days": RHR_BASELINE_DAYS,
                "score": scores["rhr"],
            },
        },
    )
