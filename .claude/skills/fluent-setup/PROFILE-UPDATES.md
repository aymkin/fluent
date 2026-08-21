# Profile Updates (existing profile)

```markdown
# 👋 Welcome back, {name}!

You already have a learning profile.

What would you like to do?

1. **Update profile** — change goals, timeline, or preferences
2. **View current plan** — see your learning schedule
3. **Reset progress** — start fresh (⚠️ erases all progress!)
4. **Cancel** — keep everything as is

**Type 1, 2, 3, or 4:**
```

- **1** — ask which field, update only that field, preserve the rest.
- **2** — render the plan section from current data. Read-only.
- **3** — confirm twice. This deletes every file in the resolved data directory. Back up first:

  ```bash
  DATA_DIR="$(python3 "${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PROJECT_DIR:-.}}/.claude/hooks/ensure_data_dir.py")"
  TS="$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$DATA_DIR/.backups/pre-reset-$TS"
  cp "$DATA_DIR"/*.json "$DATA_DIR/.backups/pre-reset-$TS/"
  ```

  Then restart setup from Step 2.
- **4** — exit cleanly.
