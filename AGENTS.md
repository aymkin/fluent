# AI Agent Integration Guide

**For non-Claude CLIs** (Codex, Gemini, and other agentic coding tools). Claude Code
loads `CLAUDE.md` and `.claude/skills/` automatically and does not need this file.

## What Fluent is

Fluent turns an agentic coding CLI into a personal language tutor. It stores the
learner's profile, mistakes, mastery levels, and FSRS-6 review schedule as JSON in the
data directory, and writes a markdown transcript of every practice session to
`/results/`. Your job is to run interactive practice sessions against that state:
present one question at a time, grade the answer, explain the correction, and persist
the result.

## What to read, in order

| Read | For |
|------|-----|
| `LEARNING_SYSTEM.md` | Session mechanics — what state to load, FSRS scheduling, session-end protocol |
| `CLAUDE.md` | Learning principles, operating rules, tutor personality, database helper scripts |
| `.claude/skills/<name>/SKILL.md` | The per-command flow (one directory per command, e.g. `.claude/skills/fluent-writing/SKILL.md`) |
| `results/README.md` | Session result file format the analyzer parses |
| `.claude/skills/fluent-db-updater/SKILL.md` | Input schema for `read-db.py` / `update-db.py` |
| `data-examples/` | JSON schema of each database |

## The one thing that differs for you

Claude Code auto-loads a `SKILL.md` when the learner types the matching slash command,
and auto-loads the helper skills (`fluent-fsrs-reference`, `fluent-feedback-formatter`,
`fluent-db-updater`, `fluent-session-analyzer`) mid-session as needed. **Other CLIs get
no such dispatch** — when the learner asks for `/fluent-writing`, read
`.claude/skills/fluent-writing/SKILL.md` yourself, and read any helper skill it
references before you rely on it.

Likewise, Fluent's hooks (SessionStart/PostToolUse) are Claude Code hooks.
Outside Claude Code they do not fire, so call
`python3 .claude/hooks/read-db.py` at session start and
`python3 .claude/hooks/update-db.py` at session end explicitly.

## Never compute review intervals by hand

Scheduling belongs to `.claude/hooks/fsrs.py`, driven by `update-db.py`. Submit a score
(0-10); the code maps it to an FSRS rating and returns the next `interval_days` /
`due_date`. Any hand-rolled interval math will diverge from the stored state.
