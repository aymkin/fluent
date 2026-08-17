# Lessons

## 2026-08-17 — jq queries against the read-db.py dump

`read-db.py` prints ~300KB, so the result is persisted to a file and has to be
queried with `jq`. Two avoidable errors:

- **exit 5** (jq runtime error) — queried `.databases.progress` / `.mistakes` /
  `.mastery`; the real keys are `progress_db`, `mistakes_db`, `mastery_db`.
  `null | keys` raises. Read key names first, don't guess.
- **exit 3** (jq compile error) — `{lvl: .a // .b}` is invalid; the `//`
  operator needs parens inside an object constructor: `{lvl: (.a // .b)}`.

Also: chaining probes with `&&` means one failure cancels the rest of the batch.
Use `;`. And `read-db.py --review` already returns a trimmed payload for
`/fluent-review` — no need to filter the full dump.
