# Data Examples Directory

Template files showing the structure of the learning data that `/fluent-setup` creates
in `/data`.

| Template File | What It Becomes | Purpose |
|--------------|-----------------|---------|
| `learner-profile-template.json` | `/data/learner-profile.json` | Your personal info, goals, preferences |
| `progress-db-template.json` | `/data/progress-db.json` | Statistics and accuracy trends |
| `mistakes-db-template.json` | `/data/mistakes-db.json` | Error patterns you're working on |
| `mastery-db-template.json` | `/data/mastery-db.json` | Skill mastery levels (0-5 stars) |
| `spaced-repetition-template.json` | `/data/spaced-repetition.json` | Review schedule (FSRS-6 algorithm) |
| `session-log-template.json` | `/data/session-log.json` | Complete session history |

## 🚫 Don't copy these into `/data`

Run `/fluent-setup` instead — it writes the real files with your information,
initialized values, and correct metadata. Values in braces (`{YOUR_NAME}`,
`{YYYY-MM-DD}`, `{A1|A2|B1|B2|C1|C2}`) are placeholders that setup fills in.

## 💡 For Developers

Templates mirror the production schema — use them for testing or when building tools.
When adding a field: update the template here, update the `/fluent-setup` skill to
populate it, update `.claude/hooks/update-db.py` if the field is written at session
end, and update the teaching docs if it affects how sessions run.
