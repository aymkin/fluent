# 🌍 Fluent
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Powered%20by-Claude%20Code-blue)](https://code.claude.com)

**The AI Language Learning Kit for Claude Code and others**

*A comprehensive set of rules, guidance, and intelligent tracking systems that transform Claude Code into your personal language tutor. Master any language through adaptive practice powered by proven cognitive science—spaced repetition, active recall, and progress tracking that learns from you.*

https://github.com/user-attachments/assets/66d68aad-210a-452d-b405-b58c13f42f53

---

> **This is a personal fork** of [m98/fluent](https://github.com/m98/fluent), maintained at
> [aymkin/fluent](https://github.com/aymkin/fluent). It tracks upstream but has diverged:
> FSRS-6 scheduling (replacing SM-2), and a trimmed
> `/fluent-review` data payload for faster response times. See [CHANGELOG.md](CHANGELOG.md)
> for the full list. The install ref is `fluent@aymkin` — the `@` suffix is the *marketplace*
> name from `.claude-plugin/marketplace.json` (`"name": "aymkin"`), not the git remote or the
> upstream author.

## 🚀 Quick Start

### 1. Install

```bash
claude plugin marketplace add aymkin/fluent && claude plugin install fluent@aymkin
```

One line. Registers the marketplace, installs the plugin. Works globally from any directory after this.

### 2. Start learning

Restart Claude Code, then:

```
/fluent-setup     # onboard: name, target language, level, goals
/fluent-learn     # begin your first session
```

That's it.

---

### Requirements

- [Claude Code](https://code.claude.com) installed
- **Python 3.8+** (most systems already have it — check with `python3 --version`). Install via [python.org](https://www.python.org/downloads/), `brew install python3`, or your distro's package manager. No pip packages needed — Fluent uses only the standard library.

### Verify, update, uninstall

```bash
claude plugin list                    # expect: fluent@aymkin  enabled
claude plugin update fluent@aymkin    # pull latest version
claude plugin uninstall fluent@aymkin # remove entirely
```

### Alternative: git clone

Prefer to hack on the skills or keep per-project state?

```bash
git clone https://github.com/aymkin/fluent.git
cd fluent
claude plugin marketplace add ./ && claude plugin install fluent@aymkin
claude          # launch from repo root
/fluent-setup
```

Learner data lives in `./data/` inside the cloned repo instead of `~/.claude/fluent-data/`.

The `marketplace add ./` step is not optional if you want the hooks. Skills load from a bare
clone, but hooks are registered only through `.claude/hooks/hooks.json`, which Claude Code
reads via the plugin manifest. Skip the step and you get the slash commands with **no
SessionStart briefing, no JSON validation, and no automatic backups**.

### Where your data lives

Fluent resolves the data directory in this order — first match wins:

1. `$FLUENT_DATA_DIR` if set (override everything).
2. `$CLAUDE_PROJECT_DIR/data/` if it has `learner-profile.json` (clone mode, running from outside the repo root).
3. `./data/` if it has `learner-profile.json` (clone mode, running inside the repo).
4. `~/.claude/fluent-data/` (plugin-install default).

Set `FLUENT_DATA_DIR` to run multiple learners on one machine:

```bash
export FLUENT_DATA_DIR=~/.fluent/dutch
```

Check where Fluent is currently looking:

```bash
python3 -c "import sys; sys.path.insert(0, '.claude/hooks'); from fluent_paths import data_dir; print(data_dir())"
```

---

## 🎮 Available Commands & Skills

Fluent is 12 Claude Code skills. The learner-facing ones are gated: they run
only when you type the slash command, so a chat message can never trigger a
20-minute session or a database write. `/fluent-progress` is read-only and also
auto-triggers on questions like "how am I doing?". The four helper skills
auto-load whenever Claude needs them mid-session. All 12 appear in your `/`
menu.

| Command | What it does |
|---------|--------------|
| `/fluent-setup` | One-time onboarding — name, language, level, goals. Creates your profile. |
| `/fluent-review` | Today's spaced-repetition queue. **Start every day here.** |
| `/fluent-learn` | Adaptive mixed practice; the AI picks what you need most. |
| `/fluent-vocab` | Flashcard drills, both directions plus cloze. |
| `/fluent-writing` | Emails, letters, forms — corrected line by line. |
| `/fluent-speaking` | Role-play conversation, typed. |
| `/fluent-reading` | Short texts plus comprehension questions. |
| `/fluent-progress` | Statistics dashboard: accuracy, streak, mastery, achievements. |
| `/fluent-fsrs-reference` | Helper — how a score becomes a review interval. |
| `/fluent-feedback-formatter` | Helper — the per-answer feedback template. |
| `/fluent-db-updater` | Helper — the session payload that writes all 6 databases. |
| `/fluent-session-analyzer` | Helper — reads `/results/*.md` to plan the next session. |

---

## 📁 System Architecture

### Data Layer (`/data` directory)

Six JSON databases, created by `/fluent-setup` and written only by
`.claude/hooks/update-db.py`: `learner-profile`, `progress-db`, `mistakes-db`,
`mastery-db`, `spaced-repetition`, `session-log`. The templates in
[`data-examples/`](data-examples/) are their schema.

**🔒 Privacy:** all data stays on your machine, excluded from git via `.gitignore`.

### Intelligence Layer

The AI follows these guides:

- **`LEARNING_SYSTEM.md`** - Complete methodology (how to teach)
- **`CLAUDE.md`** - AI tutor's role and personality
- **`AGENTS.md`** - Entry point for non-Claude CLIs (Codex, Gemini)
- **`results/README.md`** - Canonical session-file format that `fluent-session-analyzer` parses
- **`.claude/references/`** - The canonical `update-db.py` payload (`db-updater-payload.example.json`), which the `fluent-db-updater` skill points at

### Interface Layer

- **Skills** (`.claude/skills/`) — one directory per command; see the table above.
- **Plugin manifests** (`.claude-plugin/`) — `plugin.json` + `marketplace.json` make Fluent installable via `/plugin marketplace add aymkin/fluent`.
- **Automatic Hooks** (`.claude/hooks/`) — SessionStart welcome, PostToolUse JSON validation + timestamped backups. `hooks.json` is the single registration for both install paths, wired in through `plugin.json`. Backup layers and recovery: [`.claude/hooks/README.md`](.claude/hooks/README.md).
- **Session Results** (`/results/`) — Detailed practice logs per session, parsed by `fluent-session-analyzer` to plan future sessions.

---

## 🤝 Contributing

Issues and pull requests welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for setup, tests, and commit conventions.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🛠️ Troubleshooting

**`python3: command not found` when hooks run.**
Install Python 3.8+ and make sure `python3` is on your PATH. On macOS: `brew install python3`. On Debian/Ubuntu: `sudo apt install python3`. On Windows: install via [python.org](https://www.python.org/downloads/) or use WSL.

**Learner data is showing up in the wrong place.**
Check the data-dir resolution order (see above). Set `FLUENT_DATA_DIR` explicitly in your shell to force a specific location.

**JSON validation fails after a manual edit.**
The PostToolUse hook exits with status 2 if it finds malformed JSON. The last 10 backups live at `<data_dir>/<filename>.json.backup-<timestamp>`. Restore with: `cp <data_dir>/learner-profile.json.backup-XXXXXX <data_dir>/learner-profile.json`.

**Skills don't appear in the `/` menu after plugin install.**
Restart Claude Code. If still missing, verify install:

```bash
claude plugin list                              # should show fluent@aymkin enabled
claude plugin validate fluent@aymkin
```

Or from inside a session: `/plugin list`. If the plugin is disabled, enable it: `claude plugin enable fluent@aymkin`.

---

*Start your language learning journey today!* 🚀 See [Quick Start](#-quick-start) above.
