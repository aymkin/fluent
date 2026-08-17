# Fluent Hooks System

This directory contains automated hooks that manage data integrity, backups, and user feedback for the Fluent language learning system.

## 🎯 Purpose

Hooks ensure your learning data is:
- ✅ **Always backed up** - Every save is versioned, 10 generations deep per file
- ✅ **Validated** - JSON structure checked on every save
- ✅ **Tracked** - Session stats displayed automatically

## 📋 Hook Scripts

Three hooks, all registered in `hooks.json`.

### 1. `validate-data.py` (PostToolUse)

**Triggered:** After every Write/Edit operation on data files

**What it does:**
1. Checks if the modified file is in `data/*.json`
2. Validates JSON structure using Python's JSON parser
3. Creates timestamped backup: `data/file.json.backup-20231117-143022`
4. Shows success message or warning if JSON is invalid

**Example output:**
```
[Fluent] ✓ Data saved and validated: data/learner-profile.json
[Fluent] 💾 Backup created: data/learner-profile.json.backup-20231117-143022
```

**Error handling:**
- Invalid JSON triggers exit code 2, blocking the operation and alerting Claude
- Error message shown: `[Fluent] ⚠️ WARNING: Invalid JSON in data/file.json`

---

### 2. `session-end.py` (SessionEnd)

**Triggered:** When practice session ends (user exits Claude Code)

**What it does:**
1. Reads `learner-profile.json`
2. Shows current streak and total sessions

**Example output:**
```
[Fluent] 🔥 Current streak: 7 days
[Fluent] 📊 Total sessions: 42
[Fluent] 👋 Great work today!
```

This hook does **not** back anything up — the per-write backups in
`validate-data.py` already hold every state this snapshot would have copied.

---

### 3. `session-start.py` (SessionStart)

**Triggered:** When Claude Code starts a new session

**What it does:**
1. Checks if `data/learner-profile.json` exists
2. If not found, prompts user to run `/fluent-setup`
3. If found, displays:
   - Welcome message with learner's name
   - Target language and current/target level
   - Current streak
4. Checks `spaced-repetition.json` for due reviews
5. Alerts user if reviews are due today

**Example output (first time):**
```
[Fluent] 🌍 Welcome to Fluent - The AI Language Learning Kit!
[Fluent] 📝 Run /fluent-setup to create your personalized learning profile
```

**Example output (returning user):**
```
[Fluent] 🌍 Welcome back, Mohammad!
[Fluent] 📚 Learning: Spanish
[Fluent] 🎯 Level: A2 → B1
[Fluent] 🔥 Streak: 12 days
[Fluent] 📅 15 items due for review today - Run /fluent-review!
```

---

## 🔧 How It Works

### Hook Configuration

`.claude/hooks/hooks.json` is the **single** hook registration, referenced from
`.claude-plugin/plugin.json` (`"hooks": "./.claude/hooks/hooks.json"`). Commands
resolve through `${CLAUDE_PLUGIN_ROOT}`; the scripts themselves resolve the
runtime data directory via `fluent_paths.py` — `$FLUENT_DATA_DIR` →
`$CLAUDE_PROJECT_DIR/data/` → `./data/` → `~/.claude/fluent-data/`.

There used to be a second copy of the same four hooks in `.claude/settings.json`
for clone-mode installs. It was deleted: with the plugin installed *and* the repo
open as the project directory, both registrations fired and every hook ran twice
(the SessionStart banner printed twice in one startup).

**Working from a clone?** Register the clone as a local marketplace so hooks come
from `hooks.json` like everywhere else:

```bash
git clone https://github.com/aymkin/fluent.git && cd fluent
claude plugin marketplace add ./
claude plugin install fluent@aymkin
```

Data still lands in the clone's `./data/` — `fluent_paths.py` prefers it over
`~/.claude/fluent-data/` whenever `./data/learner-profile.json` exists. Cloning
*without* installing gives you the skills but no hooks, so no automatic backups.

### Hook Execution Flow

1. **Event occurs** (e.g., file is written)
2. **Claude Code triggers hook** based on matcher pattern
3. **Script receives JSON input via stdin**:
   ```json
   {
     "session_id": "abc123",
     "tool_name": "Write",
     "tool_input": {
       "file_path": "data/learner-profile.json",
       "content": "..."
     }
   }
   ```
4. **Script processes input** and performs actions
5. **Script exits with status code**:
   - `0` = Success (stdout shown in verbose mode)
   - `2` = Blocking error (stderr shown to Claude)
   - Other = Non-blocking error (logged)

### Exit Code Behavior

| Exit Code | Behavior | When to Use |
|-----------|----------|-------------|
| `0` | Success, continue normally | Validation passed, backup created |
| `2` | Block operation, show stderr to Claude | Invalid JSON, critical error |
| Other | Log error, continue anyway | Non-critical warning |

---

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

---

## 📚 Additional Resources

Writing, customizing, debugging, and configuring hooks in general — the full
event list, `claude --debug`, transcript mode, timeouts — is upstream Claude Code
documentation, not something Fluent redefines:

- [Claude Code Hooks Guide](https://code.claude.com/docs/en/hooks-guide)
- [Hooks Reference](https://code.claude.com/docs/en/hooks-reference)
- [Fluent Main README](../../README.md)
- [Learning System Guide](../../LEARNING_SYSTEM.md)


