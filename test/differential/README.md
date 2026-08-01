# Differential validation (migrate-python3)

Proves the Python 3 port behaves the same as the frozen Python 2 Docker
reference. The port's value is *stable, known* conformance behavior, so
behavioral equivalence — not "tests pass" — is the acceptance gate.

## Procedure

1. Start the **reference** fuzzingserver from the frozen Docker image on :9001,
   drive it, and keep its `reports/clients/index.json`.
2. Start the **py3** fuzzingserver (`uv run wstest -m fuzzingserver`) on :9001,
   drive it with `run_fuzzingserver.py`, keep its `index.json`.
3. Diff:

   ```
   python test/differential/normalize_reports.py \
       reference/index.json py3/index.json --triage test/differential/triage.json
   ```

   Exit 0 = equivalent (or every difference is triaged). Exit 1 = untriaged
   behavioral difference — a port bug to fix or a difference to document.

## Triage

`triage.json` maps a caseId to a short reason for an *accepted* difference
(e.g. a permessage-deflate negotiation change between autobahn versions).
Only add an entry after confirming the difference is an environment artifact,
not a port bug.

## Status

The py3 port currently passes the full non-compression, non-limits suite
(sections 1-8, 10, 11 = 247 cases: 244 OK / 3 informational / 0 fail / 0
exceptions) against a conformant asyncio echo testee. Sections 9 (limits),
12 and 13 (permessage-deflate) still need a full reference-vs-py3 diff run
(requires the Docker image); 12/13 are the flagged drift risk.
