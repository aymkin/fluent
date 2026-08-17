# Data Directory

Your six learning databases live here — but only in **clone mode**. A plugin
install keeps them in `~/.claude/fluent-data/` instead, and `$FLUENT_DATA_DIR`
overrides both. Ask Fluent where it is actually looking:

```bash
python3 -c "import sys; sys.path.insert(0, '.claude/hooks'); from fluent_paths import data_dir; print(data_dir())"
```

`/fluent-setup` creates all six on first run: `learner-profile.json`,
`progress-db.json`, `mistakes-db.json`, `mastery-db.json`,
`spaced-repetition.json`, `session-log.json`.

## Schema

`data-examples/` holds a template per database — those files *are* the schema,
kept in step with `.claude/hooks/update-db.py`. Read them rather than a copy.

## Privacy

Everything here stays on your machine and is excluded from git (`.gitignore`
covers `*.json`, the rotating `*.backup-*` files, and `.backups/`).

## Handling

- **Don't hand-edit.** `update-db.py` owns these files; a hand-written value
  diverges from what the script recomputes next session.
- **To back up:** copy the whole directory. The automatic backups live *inside*
  it, so they don't survive losing it.
- **To reset:** delete the `.json` files and run `/fluent-setup` again.

Recovering from a bad write: see `.claude/hooks/README.md`.
