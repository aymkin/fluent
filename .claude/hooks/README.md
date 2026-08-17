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

```bash
ls -t data/learner-profile.json.backup-* | head -1        # newest single-file backup
ls -t data/.backups/pre-update-*/                         # newest full-set snapshot
cp data/learner-profile.json.backup-20231117-143022 data/learner-profile.json
```

---

## 🛠️ Customization

### Adding Custom Validation

Edit `validate-data.py` to add custom validation logic:

```python
# Example: Validate specific field exists
if file_path == "data/learner-profile.json":
    if "learner" not in data or "target_language" not in data["learner"]:
        print("[Fluent] ⚠️ Missing required field: target_language", file=sys.stderr)
        sys.exit(2)  # Block operation
```

### Adding Session Analytics

Edit `session-end.py` to add custom analytics:

```python
# Example: Calculate accuracy trend
progress_path = data_dir() / "progress-db.json"
if progress_path.exists():
    with open(progress_path, 'r') as f:
        progress = json.load(f)

    accuracy = progress.get("overall_stats", {}).get("accuracy_rate", 0)
    print(f"[Fluent] 📈 Overall accuracy: {accuracy:.1%}")
```

### Adding New Hooks

To add a new hook type:

1. **Create script** in `.claude/hooks/your-hook.py`
2. **Make it executable**: `chmod +x .claude/hooks/your-hook.py`
3. **Add to `hooks.json`** (the only registration — do not add a second copy elsewhere):
   ```json
   {
     "hooks": {
       "YourHookEvent": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/.claude/hooks/your-hook.py\""
             }
           ]
         }
       ]
     }
   }
   ```

---

## 🔍 Debugging Hooks

### Enable Debug Mode

Run Claude Code with debug flag:
```bash
claude --debug
```

This shows detailed hook execution logs:
```
[DEBUG] Executing hooks for PostToolUse:Write
[DEBUG] Hook command: .claude/hooks/validate-data.py
[DEBUG] Hook completed with status 0
```

### View Hook Output

Enable verbose mode during session:
- Press **Ctrl+O** to toggle transcript mode
- Shows all hook stdout/stderr output

### Test Hooks Manually

You can test hooks directly:

```bash
# Test validate-data hook
echo '{"tool_name":"Write","tool_input":{"file_path":"data/test.json"}}' | python3 .claude/hooks/validate-data.py

# Test session-start hook
echo '{}' | python3 .claude/hooks/session-start.py

# Test session-end hook
echo '{}' | python3 .claude/hooks/session-end.py
```

---

## 📊 Hook Events Reference

| Hook Event | When It Fires | Use Case |
|------------|---------------|----------|
| `PostToolUse` | After Write/Edit/Read/etc | **Used by Fluent** — validation + backups |
| `SessionEnd` | When session ends | **Used by Fluent** — session summary |
| `SessionStart` | When session starts | **Used by Fluent** — welcome + due reviews |
| `PreCompact` | Before compaction | Unused — nothing writes to `data/` during compaction |
| `UserPromptSubmit` | Before processing user input | Unused |
| `PreToolUse` | Before tool execution | Unused |

---

## 🚨 Troubleshooting

### Hook Not Running

**Problem:** Hook doesn't execute
**Solution:**
1. Check hook is registered: `grep hooks .claude/hooks/hooks.json`
2. Confirm the plugin is installed (`claude plugin list`) — hooks.json is only
   read for plugin installs; a bare clone registers nothing
3. Verify script is executable: `ls -la .claude/hooks/`
4. Test script manually (see "Test Hooks Manually" above)

### Invalid JSON Error

**Problem:** `[Fluent] ⚠️ WARNING: Invalid JSON`
**Solution:**
1. Check the last backup: `ls -t data/*.backup-* | head -1`
2. Validate JSON: `python3 -m json.tool data/file.json`
3. Restore from backup if needed: `cp data/file.json.backup-XXXXXX data/file.json`

### Permission Denied

**Problem:** `Permission denied` when running hook
**Solution:**
```bash
chmod +x .claude/hooks/*.py
```

### Hook Timeout

**Problem:** Hook times out (default 60s)
**Solution:** Increase timeout in `hooks.json`:
```json
{
  "type": "command",
  "command": "...",
  "timeout": 120
}
```

---

## 📚 Additional Resources

- [Claude Code Hooks Documentation](https://code.claude.com/docs/en/hooks-guide)
- [Hooks Reference](https://code.claude.com/docs/en/hooks-reference)
- [Fluent Main README](../../README.md)
- [Learning System Guide](../../LEARNING_SYSTEM.md)


