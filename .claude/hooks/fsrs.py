"""FSRS-6 spaced-repetition scheduler — stdlib-only port.

Ported from py-fsrs's `Scheduler` (https://github.com/open-spaced-repetition/
py-fsrs); PINNED fsrs==6.3.1. DEFAULT_W is the 21-float parameter vector
printed from the pinned package in Task 2 Step 1 (do NOT hand-edit):

    .devvenv/bin/python -c \
        "from fsrs import Scheduler; print(list(Scheduler().parameters))"

Correctness gate: tests/test_fsrs_crosscheck.py must match py-fsrs's
Scheduler within tolerance.

Scope note: this module only models day-granularity, "long-term" reviews.
`item` stores a last-reviewed *date* (not a timestamp), so py-fsrs's
same-day/short-term path (`Scheduler._short_term_stability`, driven by
w[17]-w[19] and sub-day learning/relearning steps) is intentionally not
ported — there is no sub-day state to feed it. The cross-check configures
py-fsrs's Scheduler with empty learning/relearning steps so every review
goes through the same long-term formulas implemented here.
"""
import math
from datetime import date, timedelta

DEFAULT_W = [
    0.212,
    1.2931,
    2.3065,
    8.2956,
    6.4133,
    0.8334,
    3.0194,
    0.001,
    1.8722,
    0.1666,
    0.796,
    1.4835,
    0.0614,
    0.2629,
    1.6483,
    0.6014,
    1.8729,
    0.5425,
    0.0912,
    0.0658,
    0.1542,
]

TARGET_RETENTION = 0.90
_S_MIN = 0.001  # fsrs.scheduler.STABILITY_MIN
_D_MIN = 1.0  # fsrs.scheduler.MIN_DIFFICULTY
_D_MAX = 10.0  # fsrs.scheduler.MAX_DIFFICULTY


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _decay(w):
    return -w[20]


def _factor(w):
    d = _decay(w)
    return 0.9 ** (1.0 / d) - 1.0


def retrievability(elapsed_days, stability, w=DEFAULT_W):
    """Predicted probability of recall after `elapsed_days` at `stability`."""
    return (1.0 + _factor(w) * max(elapsed_days, 0) / stability) ** _decay(w)


def interval_from_stability(stability, w=DEFAULT_W):
    """Days until retrievability decays to TARGET_RETENTION."""
    d = _decay(w)
    return (stability / _factor(w)) * (TARGET_RETENTION ** (1.0 / d) - 1.0)


def _d0(w, g):
    """Raw (unclamped) initial-difficulty curve D0(g)."""
    return w[4] - math.exp(w[5] * (g - 1)) + 1.0


def _init_stability(w, g):
    return max(w[g - 1], _S_MIN)


def _init_difficulty(w, g):
    return _clamp(_d0(w, g), _D_MIN, _D_MAX)


def _next_difficulty(w, d, g):
    delta = -w[6] * (g - 3)
    damped = d + delta * (10.0 - d) / 9.0  # linear damping
    # Mean-revert toward D0(Easy). py-fsrs computes this target *unclamped*
    # (Scheduler._next_difficulty calls _initial_difficulty(clamp=False)) —
    # only the final result is clamped.
    reverted = w[7] * _d0(w, 4) + (1.0 - w[7]) * damped
    return _clamp(reverted, _D_MIN, _D_MAX)


def _next_stability_recall(w, d, s, r, g):
    hard = w[15] if g == 2 else 1.0
    easy = w[16] if g == 4 else 1.0
    return s * (
        1.0
        + math.exp(w[8])
        * (11.0 - d)
        * (s**-w[9])
        * (math.exp((1.0 - r) * w[10]) - 1.0)
        * hard
        * easy
    )


def _next_stability_forget(w, d, s, r):
    long_term = (
        w[11] * (d**-w[12]) * ((s + 1.0) ** w[13] - 1.0) * math.exp((1.0 - r) * w[14])
    )
    # py-fsrs caps a lapse's stability drop at s / exp(w[17]*w[18]) (its
    # "short-term" forget bound), not merely at s itself.
    short_term_cap = s / math.exp(w[17] * w[18])
    return min(long_term, short_term_cap)


def _parse(d):
    return date.fromisoformat(d)


def schedule(item, rating, today, weights=None):
    """Advance one FSRS-6 review step for a day-granularity `item`.

    item reads: stability (float|None), difficulty (float|None),
    last_reviewed ("YYYY-MM-DD"|None). rating is 1..4 (Again/Hard/Good/Easy).
    Returns {"stability", "difficulty", "interval_days", "due_date"}.
    """
    w = weights if weights else DEFAULT_W
    s = item.get("stability")
    d = item.get("difficulty")
    if s is None or d is None:
        # New card: initialize from the first rating.
        s2 = _init_stability(w, rating)
        d2 = _init_difficulty(w, rating)
    else:
        last = item.get("last_reviewed") or today
        elapsed = max((_parse(today) - _parse(last)).days, 0)
        r = retrievability(elapsed, s, w)
        d2 = _next_difficulty(w, d, rating)
        if rating == 1:
            s2 = _next_stability_forget(w, d, s, r)
        else:
            s2 = _next_stability_recall(w, d, s, r, rating)
    s2 = max(s2, _S_MIN)
    interval = max(1, round(interval_from_stability(s2, w)))
    due = _parse(today) + timedelta(days=interval)
    return {
        "stability": round(s2, 4),
        "difficulty": round(d2, 4),
        "interval_days": interval,
        "due_date": due.isoformat(),
    }


if __name__ == "__main__":  # smoke self-check
    assert abs(retrievability(5, 5) - 0.9) < 0.01
    it = {"stability": 5.0, "difficulty": 5.0, "last_reviewed": "2026-01-01"}
    assert schedule(it, 3, "2026-01-06")["stability"] > 5.0
    assert schedule(it, 1, "2026-01-06")["interval_days"] == 1
    print("fsrs.py self-check OK")
