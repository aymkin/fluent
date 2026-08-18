# Data Examples Directory

Each `<name>-template.json` here is the schema for the `<name>.json` that
`/fluent-setup` writes into the resolved data directory.

## 🚫 Don't copy these into `/data`

Run `/fluent-setup` instead — it writes the real files with your information,
initialized values, and correct metadata. Values in braces (`{YOUR_NAME}`,
`{YYYY-MM-DD}`, `{A1|A2|B1|B2|C1|C2}`) are placeholders that setup fills in.

## 💡 For Developers

Templates mirror the production schema — use them for testing or when building tools.
When adding a field: update the template here, update the `/fluent-setup` skill to
populate it, update `.claude/hooks/update-db.py` if the field is written at session
end, and update the teaching docs if it affects how sessions run.
