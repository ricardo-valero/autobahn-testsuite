# Differential validation (migrate-python3)

Proves the Python 3 port behaves the same as the frozen Python 2 reference.
The port's value is *stable, known* conformance behavior, so behavioral
equivalence — not "tests pass" — is the acceptance gate.

**Frozen reference** = the immutable published image
`crossbario/autobahn-testsuite:25.10.1` (Docker Hub, published 2025-10-07),
matching the `v25.10.1-py2` git tag. Master no longer builds a Docker image;
this published image is the only Docker artifact the workflow still touches,
and only to capture reference reports (see fixtures under `reference/`).

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

## Status — validated

A full differential run was performed (2026-08-02): the frozen py2 image and
the py3 port were each driven by the same asyncio echo testee with an identical
spec, and their reports compared with `normalize_reports.py`.

**Result: 247 cases (sections 1-8, 10, 11), 0 differences.** The py3 port
produces byte-identical verdicts (behavior, close behavior, remote close code)
to the frozen Python 2 reference. The migration is proven behaviorally faithful
for the non-compression, non-limits suite.

The captured reference is committed as a Docker-free fixture:
`reference/index-sections-1-8-10-11.json`. To re-verify without Docker, run the
py3 fuzzingserver, drive it with `run_fuzzingserver.py --agent diffcheck`, then:

```
python normalize_reports.py reference/index-sections-1-8-10-11.json <py3>/index.json
```

### Sections 12/13 (permessage-deflate) — also validated

A second run (2026-08-03) covered the compression cases, the flagged drift
risk. **Result: 216 cases (sections 12, 13), 0 differences** — all "OK" with
close code 1000 on both the frozen py2 reference and the py3 port.

Getting there found and fixed a real port bug the echo testee could never
reach: the 12/13 case bodies read testdata via `open(fn, b'rb')` — a bytes
mode literal that raises under py3 (`open() argument 'mode' must be str, not
bytes`). Only a permessage-deflate-negotiating testee exercises those bodies,
so the compression follow-up was what surfaced it.

Two testee wrinkles worth recording:
- The canonical [`testee_client_aio.py`](https://github.com/crossbario/autobahn-python/blob/master/wstest/testee_client_aio.py)
  offers deflate on *every* connection, including `/getCaseCount`. The 2015-era
  py2 server (autobahn 0.10.9) can't complete that control-plane exchange over
  deflate with a 2026 client, so the count never arrives and the testee crashes.
  This is version-skew interop, not a port defect.
- `diff_driver_deflate.py` (committed here) works against both: it fetches the
  count on a *plain* connection and offers deflate only on `/runCase`. Use it
  for both sides of the compression diff.

`reference/index-sections-12-13.json` is the committed Docker-free fixture.

### Remaining

Section 9 (limits) passes standalone on py3 but was excluded from the diff for
runtime (large/slow payloads). Everything else — 463 cases across sections 1-8,
10, 11, 12, 13 — is proven byte-identical to the frozen py2 reference.
