# Fluent Hooks System

Two hooks keep your learning data validated and backed up. Both are registered
in `hooks.json`; the scripts alongside them are called directly by the skills.

## 📋 What runs

### `validate-data.py` — PostToolUse (`Write|Edit`)

Validates any `*.json` written inside the resolved data directory, then copies
it to `<file>.json.backup-<timestamp>` and rotates all but the 10 newest.
Malformed JSON exits `2`, which blocks the write and shows the error to Claude:

```
[Fluent] ⚠️  WARNING: Invalid JSON in data/learner-profile.json
```

### `session-start.py` — SessionStart

Prints the learner's name, language, level and streak, and counts items due
today from `spaced-repetition.json`. With no profile yet, it points at
`/fluent-setup` instead.

### Called by skills, not by hooks

`read-db.py` (loads all six databases), `update-db.py` (writes all six at
session end), `fsrs.py` (the FSRS-6 scheduler), `fluent_paths.py` (path
resolution), `ensure_data_dir.py` (prints the data dir, creating it if needed).

## 🔧 Registration

`.claude/hooks/hooks.json` is the **single** hook registration, referenced from
`.claude-plugin/plugin.json` (`"hooks": "./.claude/hooks/hooks.json"`). Commands
resolve through `${CLAUDE_PLUGIN_ROOT}`; the scripts themselves resolve the
runtime data directory via `fluent_paths.py` (see its docstring for the
precedence order).

**Working from a clone?** Register the clone as a local marketplace, or you get
the skills with no hooks and no automatic backups — see
[Alternative: git clone](../../README.md#alternative-git-clone).

## 📂 Backup Strategy

Two layers, each covering a write path the other cannot see:

### Layer 1: Per-save versions (`validate-data.py`, PostToolUse)
- **Location:** `data/<file>.json.backup-YYYYMMDD-HHMMSS`
- **Created:** After every `Write`/`Edit` to a `*.json` inside the resolved data dir,
  holding the state that was just saved
- **Retention:** 10 most recent per file, older ones auto-rotated out
- **Covers:** single-file edits made through Claude — roll back up to 10 saves

### Layer 2: Pre-update snapshots (`update-db.py`, not a hook)
- **Location:** `data/.backups/pre-update-<session_id>/`
- **Created:** Before `update-db.py` mutates all six databases at session end
- **Retention:** Manual cleanup (one directory per session)
- **Covers:** the only multi-file mutation, where a partial write could desync files

Layer 1 hangs off the `Write`/`Edit` tool call, so it never sees `update-db.py`'s
writes; Layer 2 lives inside that script, so it never sees a tool-call edit.
Neither is redundant. Edits made outside Claude Code (your own text editor) fire
nothing — Layer 1's most recent version is your rollback point there.

**All backups are excluded from git via `.gitignore`.** They also all live inside
the data directory, so they are not protection against losing that directory —
copy it elsewhere if you want off-box durability.

### Restoring

`[Fluent] ⚠️ WARNING: Invalid JSON in data/<file>.json` means `validate-data.py`
blocked the write. Learner data is gitignored, so these backups are the only
recovery path:

```bash
python3 -m json.tool data/<file>.json                     # see what's broken
ls -t data/<file>.json.backup-* | head -1                 # newest single-file backup
ls -t data/.backups/pre-update-*/                         # newest full-set snapshot
cp data/<file>.json.backup-YYYYMMDD-HHMMSS data/<file>.json
```

## 📚 Additional Resources

Writing, customizing, debugging, and configuring hooks in general — the full
event list, `claude --debug`, transcript mode, timeouts — is upstream Claude Code
documentation, not something Fluent redefines:

- [Claude Code Hooks Guide](https://code.claude.com/docs/en/hooks-guide)
- [Hooks Reference](https://code.claude.com/docs/en/hooks-reference)
- [Fluent Main README](../../README.md)
