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

**Still open — sections 9, 12, 13.** Section 9 (limits) passes standalone but
was excluded from the diff for runtime. Sections 12/13 (permessage-deflate,
the flagged drift risk) need a *canonical* deflate testee
([autobahn-python's `testee_client_aio.py`](https://github.com/crossbario/autobahn-python/blob/master/wstest/testee_client_aio.py))
for a trustworthy diff — a hand-rolled deflate echo client is both slow over
section 13's hundreds of cases and of unverified conformance, so any difference
it surfaces can't be attributed to the port vs. the testee. Follow-up.
