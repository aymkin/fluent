"""
The session cap — the most graded exercises one Fluent session holds.

Set by the learner on 2026-10-06: long sessions put them off starting one. At
about a minute per review item — the prompt clock measured 29 items in 29
minutes and 13 in 13 (sessions 028 and 029) — a full round takes ten minutes.

read-db.py cuts the /fluent-review round to it and publishes it to the skills as
`computed.session_cap`; session-start.py sizes today's round with it. Both are
hyphenated scripts that cannot be imported, so the number lives here.
"""

SESSION_CAP = 10
