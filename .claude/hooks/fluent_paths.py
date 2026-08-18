"""
Fluent path resolution — supports dual-mode (clone vs plugin install).

Data directory resolution precedence:
  1. $FLUENT_DATA_DIR if set (absolutized)
  2. $CLAUDE_PROJECT_DIR/data if that dir holds learner-profile.json (clone mode, non-repo cwd)
  3. ./data if ./data/learner-profile.json exists (clone mode, in-repo cwd)
  4. ~/.claude/fluent-data (plugin-mode fallback)

data_dir() is a pure resolver and does not create anything; call
ensure_data_dir() before writing.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def force_utf8_io() -> None:
    """Make stdout/stderr UTF-8 so emoji/CJK output doesn't crash on Windows.

    Windows consoles default to a legacy code page (cp1252/gbk); printing the
    emoji in the hook summaries raises UnicodeEncodeError there. No-op on
    platforms whose streams are already UTF-8 or predate ``reconfigure``.
    Call once at the top of any hook that prints.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def data_dir() -> Path:
    """Resolve the runtime data directory (pure — does not create it)."""
    env = os.environ.get("FLUENT_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()

    project = os.environ.get("CLAUDE_PROJECT_DIR")
    if project:
        candidate = (Path(project) / "data").resolve()
        if (candidate / "learner-profile.json").exists():
            return candidate

    cwd_data = (Path.cwd() / "data").resolve()
    if (cwd_data / "learner-profile.json").exists():
        return cwd_data

    return (Path.home() / ".claude" / "fluent-data").resolve()


def ensure_data_dir() -> Path:
    """Resolve the data directory and create it if missing. Call before writing."""
    d = data_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def ensure_backups_dir() -> Path:
    """Resolve the backups directory and create it if missing. Nested inside
    data_dir so the plugin-mode fallback doesn't collide with other plugins in
    the shared ~/.claude/."""
    b = data_dir() / ".backups"
    b.mkdir(parents=True, exist_ok=True)
    return b
