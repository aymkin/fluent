#!/usr/bin/env python3
"""
Fluent Session End Hook
Displays the session summary (streak + total sessions).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fluent_paths import data_dir, force_utf8_io  # noqa: E402

force_utf8_io()


def main():
    try:
        json.load(sys.stdin)
    except json.JSONDecodeError:
        pass

    profile_path = data_dir() / "learner-profile.json"
    if profile_path.exists():
        try:
            with open(profile_path, 'r') as f:
                profile = json.load(f)

            streak = profile.get("current_streak_days", 0)
            total_sessions = profile.get("total_sessions", 0)

            print(f"[Fluent] 🔥 Current streak: {streak} days")
            print(f"[Fluent] 📊 Total sessions: {total_sessions}")
            print(f"[Fluent] 👋 Great work today!")

        except Exception as e:
            print(f"[Fluent] Could not read stats: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
