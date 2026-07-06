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
    """Fit FSRS-6 weights. Imports fsrs-optimizer lazily (torch, venv-only).

    fsrs-optimizer 6.5.0 reads ./revlog.csv from the cwd with columns
    card_id, review_time (epoch ms), review_rating (1-4), then runs
    create_time_series -> define_model -> pretrain -> train; fitted
    weights land in Optimizer.w (train() itself returns plots).
    """
    import csv, tempfile
    from datetime import datetime, timezone
    from fsrs_optimizer import Optimizer  # noqa: import isolated to venv

    with tempfile.TemporaryDirectory() as td:
        with open(Path(td) / "revlog.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["card_id", "review_time", "review_rating"])
            for cid, day, rating in logs:
                dt = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                w.writerow([cid, int(dt.timestamp() * 1000), rating])
        cwd = os.getcwd()
        os.chdir(td)  # the package hardcodes ./revlog.csv
        try:
            opt = Optimizer()
            opt.create_time_series("Europe/Amsterdam", "2006-01-01", 4)
            opt.define_model()
            opt.pretrain(verbose=False)
            opt.train(verbose=False)
        finally:
            os.chdir(cwd)
    return [float(x) for x in opt.w]


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
