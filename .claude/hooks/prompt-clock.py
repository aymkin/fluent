#!/usr/bin/env python3
"""
Fluent Prompt Clock Hook
Records one timestamp per prompt so a session's length can be measured
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prompt_clock import record  # noqa: E402


def main():
    # Nothing here may reach stdout: a UserPromptSubmit hook's output is added
    # to the model's context, so a stray line would land in the learner's
    # conversation. And nothing may fail loudly either — this runs on every
    # prompt the learner sends, so a broken clock must cost a measurement, not
    # the prompt.
    try:
        payload = json.load(sys.stdin)
        sid = payload.get("session_id") or os.environ.get("CLAUDE_CODE_SESSION_ID")
        prompt = payload.get("prompt") or payload.get("message") or ""
        record(sid, is_command=prompt.lstrip().startswith("/fluent"))
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
