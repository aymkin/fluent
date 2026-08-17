# Contributing to Fluent

This is a personal fork of [m98/fluent](https://github.com/m98/fluent), maintained at
[aymkin/fluent](https://github.com/aymkin/fluent). Issues and pull requests are welcome.

## Prerequisites

- [Claude Code](https://code.claude.com)
- **Python 3.8+** — the hooks and the FSRS scheduler use the standard library only. No pip install step.
- Git

## Getting set up

```bash
git clone https://github.com/aymkin/fluent.git
cd fluent
git checkout -b feature/your-feature-name
claude          # launch from repo root
/fluent-setup   # exercise the system end to end
```

## Running the tests

There is no pytest dependency and `tests/` is not a package — each test file is a standalone
`unittest` script. Run them all from the repo root:

```bash
for t in tests/test_*.py; do echo "=== $t"; python3 "$t" -q; done
```

All of them must pass before you open a pull request.

## Commit messages

Conventional commits: `<type>(<scope>): <subject>`, with `feat`, `fix`, `docs`, `style`,
`refactor`, `test`, or `chore` as the type. For example:

```
fix(spaced-repetition): correct FSRS-6 interval calculation
```

## Never commit personal data

`data/` and `results/` hold the learner's own practice history. Both are gitignored and must
stay that way — check `git status` before committing.

## Resources

- [README](README.md) — install, architecture, and usage
- [LEARNING_SYSTEM.md](LEARNING_SYSTEM.md) — the tutoring methodology
- [FSRS Algorithm](https://github.com/open-spaced-repetition/fsrs4anki/wiki) — the scheduler Fluent uses
- [Issues](https://github.com/aymkin/fluent/issues)
