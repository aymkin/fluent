"""
The session cap — the most graded exercises one Fluent session holds — and the
review round, the most cards one /fluent-review session serves.

SESSION_CAP was set by the learner on 2026-10-06: long sessions put them off
starting one. REVIEW_ROUND was raised to 15 by the learner on 2026-11-15, for
/fluent-review only; every other session keeps SESSION_CAP. At about a minute
per review item — the prompt clock measured 29 items in 29 minutes and 13 in 13
(sessions 028 and 029) — a full review round takes fifteen minutes.

read-db.py cuts the /fluent-review round to REVIEW_ROUND and publishes both to
the skills as `computed.session_cap` and `computed.review_round`;
session-start.py sizes today's round with REVIEW_ROUND. Both are hyphenated
scripts that cannot be imported, so the numbers live here.
"""

SESSION_CAP = 10
REVIEW_ROUND = 15
