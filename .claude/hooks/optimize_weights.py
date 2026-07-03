#!/usr/bin/env python3
"""Weekly FSRS-6 weight optimizer (offline, guarded).

stdlib for extract/guard/persist; `fsrs-optimizer` (torch) only inside train().
Run from the optimizer venv: <venv>/bin/python optimize_weights.py
"""
import json, os, shutil, sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fluent_paths import ensure_data_dir, ensure_backups_dir, force_utf8_io

MIN_TOTAL = 400
MIN_NEW = 50
EXPECTED_WEIGHTS = 21


def _rating(entry):
    q = entry.get("quality", 3)  # ignore score: historical score is unreliably 0
    return 1 if q < 3 else 2 if q == 3 else 3 if q == 4 else 4


def extract_logs(sr):
    logs = []
    for cid, card in sr.get("items", {}).items():
        for e in card.get("review_history", []):
            logs.append((cid, e.get("date"), _rating(e)))
    return logs, len(logs)


def should_optimize(total, meta):
    return total >= MIN_TOTAL and (total - meta.get("reviews_at_last_optimize", 0)) >= MIN_NEW


def train(logs):
    """Fit FSRS-6 weights. Imports fsrs-optimizer lazily (torch).

    NOTE: fsrs-optimizer is not installed and the guard above prevents this
    from ever running against current data (165 < 400 reviews). The exact
    Optimizer API (constructor args, log format, .optimize() signature) is
    reconciled during venv provisioning, a later deferred task. This shape
    follows fsrs-optimizer's documented usage: a FSRSItem/FSRSReviewLog-style
    log feed into Optimizer, producing a fitted weight vector.
    """
    from fsrs_optimizer import Optimizer  # noqa: import isolated to venv
    opt = Optimizer()
    weights = opt.optimize(logs)  # adapt to fsrs-optimizer's actual API at impl time
    return [float(x) for x in weights]


def main(dry_data=None):
    force_utf8_io()
    data = ensure_data_dir()
    sr_path = data / "spaced-repetition.json"
    sr = dry_data if dry_data is not None else json.loads(sr_path.read_text(encoding="utf-8"))
    meta = sr.setdefault("metadata", {})
    logs, total = extract_logs(sr)

    if not should_optimize(total, meta):
        print(f"[optimize] insufficient data ({total}/{MIN_TOTAL}, "
              f"+{total - meta.get('reviews_at_last_optimize', 0)} new) — no-op")
        return 0
    if dry_data is not None:
        return 0

    try:
        weights = train(logs)
    except Exception as exc:  # broken venv/import must never corrupt scheduling
        print(f"[optimize] training failed, keeping current weights: {exc}", file=sys.stderr)
        return 1
    if len(weights) != EXPECTED_WEIGHTS:
        print(f"[optimize] expected {EXPECTED_WEIGHTS} weights, got {len(weights)} — abort",
              file=sys.stderr)
        return 1

    backups = ensure_backups_dir()
    dest = backups / f"pre-optimize-{date.today().isoformat()}"
    dest.mkdir(parents=True, exist_ok=True)
    for f in data.glob("*.json"):
        shutil.copy2(f, dest / f.name)

    old = meta.get("weights")
    meta["weights"] = weights
    meta["last_optimized"] = date.today().isoformat()
    meta["reviews_at_last_optimize"] = total
    tmp = sr_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(sr, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, sr_path)
    print(f"[optimize] weights updated ({total} reviews). old={old} new={weights}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
