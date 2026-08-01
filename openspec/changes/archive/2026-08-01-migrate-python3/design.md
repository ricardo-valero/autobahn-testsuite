# Design: migrate-python3

## Context

The fuzzer works by subclassing autobahn 0.10.9's protocol internals: `fuzzing.py` overrides frame-level hooks on `WebSocketServerProtocol`/`WebSocketClientProtocol` (e.g. `sendFrame`, close-handshake internals) to deliberately emit malformed frames, and imports `autobahn.websocket.utf8validator` directly. The 143 case files in `case/` construct raw frame payloads as py2 `str`. Modern autobahn (25.x) descends from the same code lineage — its `autobahn.twisted.websocket` still exposes `WebSocketServerProtocol`, `sendFrame`, `utf8validator`, and the compress API — but 10 years of drift means every overridden hook must be audited, not assumed.

The suite's value is *stable, known behavior*: implementers compare reports over years. Any port that silently changes what test 6.4.2 sends on the wire destroys that value. So behavioral equivalence, not "tests pass", is the acceptance criterion.

Groundwork already verified: WAMP/wsperf modules are commented out of `wstest.py` and `__init__.py` (dead code); only the `serializer` mode still imports WAMP internals; `fuzzing.py` has no WAMP coupling.

## Goals / Non-Goals

**Goals:**
- `wstest` (9 kept modes) running on CPython 3.12+ with uv-managed packaging.
- Provable behavioral equivalence with the frozen Docker reference for the fuzzing modes (the product), demonstrated by report diffing.
- Modern dependency stack with a committed lockfile; no EOL interpreters or insecure OpenSSL in the py3 path.

**Non-Goals:**
- Preserving WAMP/wsperf/serializer functionality (dead or unportable; removed).
- Changing test-case semantics, adding cases, or "fixing" quirks the reference implementation exhibits — bug-for-bug compatibility wins during this change.
- Retiring the py2 environment, frozen Docker image, or `add-nix-dev-env` py2 toolchain (follow-up change after validation).
- Publishing to PyPI (separate release decision).

## Decisions

### Decision 1: Migrate to modern autobahn (pinned), do not vendor 0.10.9

*Alternative considered — vendor*: copy autobahn 0.10.9's websocket package into this repo and port it alongside. Maximum fidelity, but it means porting an additional ~10k LOC of the exact code modern autobahn already ported, and owning it forever.

Modern autobahn is the descendant of the code the fuzzer subclasses; the hooks largely survive. The plan: audit every autobahn symbol the testsuite touches (imports + overridden methods), map to the modern API, and shim locally where signatures moved. **Escape hatch**: if the audit finds a hook that modern autobahn removed and cannot be reintroduced via subclassing, vendor only that piece (e.g. a single protocol method), not the whole package. Differential validation (Decision 4) is what makes this choice safe.

### Decision 2: Bytes discipline as an explicit migration phase

In py2, frame payloads flow through the code as `str`. A naive 2to3 pass turns wire payloads into py3 `str` (unicode) and corrupts every binary test case. The port therefore treats the bytes/str boundary as its own phase: payload-carrying paths (`fuzzing.py` frame construction, `case/*.py` payload literals, masking/chopping helpers) become `bytes`; human-facing strings (reports, logs, JSON) stay `str`. Case files are ported with a small set of mechanical rewrite rules (payload literals `"..."` → `b"..."`, `chr()` → `bytes([...])`, string concat → bytes concat) applied uniformly across all 143 files, then spot-audited.

### Decision 3: pyproject.toml + uv, py3.12 floor

Single `pyproject.toml` (PEP 621) with `[project]` metadata, `uv.lock` committed, `uv run wstest` as the dev entry point, hatchling (or uv_build) backend. Dependencies pinned by lock, not by `==` pins in metadata. The `justfile` gains py3 recipes alongside (not replacing) the py2 ones. Python 3.12 floor: modern Twisted/autobahn support it, and it avoids carrying compatibility shims for older 3.x.

### Decision 4: Differential validation against the frozen Docker image

The acceptance harness, in order of signal strength:
1. **Report equivalence (primary)**: run frozen-image `wstest -m fuzzingserver` and py3 `wstest -m fuzzingserver` with identical specs; run the same testee client (autobahn-python's `testee_client_aio.py`) against each; normalize the JSON reports (strip timestamps/durations/versions) and diff. Gate: identical case outcomes (pass/fail/non-strict) and identical close codes for all ~520 cases.
2. **Fuzzing-client symmetry**: same procedure with `-m fuzzingclient` against a reference echo/testee server.
3. **Wire-level spot checks (secondary)**: for a sample of byte-sensitive cases (masking, fragmentation, UTF-8 torture section 6), capture actual frames sent by both servers and compare, catching payload corruption that a lenient testee might absorb.

Differences are triaged: port bug (fix) vs py2/py3 environment artifact (document, accept explicitly). The normalizer and diff scripts live in `test/differential/` and stay in the repo as regression tooling.

### Decision 5: Dead code removed, not ported

`serializer.py` (WAMP), `wamptestee.py`, `wamptestserver.py`, `wampfuzzing.py`, `wsperfcontrol.py`, `wsperfmaster.py` are deleted. `testdb.py`, `testrun.py`, `rinterfaces.py`, `interfaces.py` are audited first: anything unreachable from the 9 kept modes is deleted rather than ported. Porting dead code is pure risk.

## Risks / Trade-offs

- [Modern autobahn removed/renamed a hook the fuzzer overrides] → symbol audit happens first (task 1.x) so surprises surface before bulk porting; per-symbol vendoring escape hatch.
- [Silent behavioral drift that reports don't reveal (e.g. both servers mark a case "pass" but send different bytes)] → wire-level spot checks on byte-sensitive sections (Decision 4.3).
- [143 case files is a large mechanical surface; a missed `str` literal corrupts one case quietly] → uniform rewrite rules + the per-case report diff catches any case whose outcome shifts.
- [permessage-deflate behavior differs across autobahn versions (cases 12.*/13.*)] → include 12.*/13.* in differential runs explicitly; if the modern extension negotiates differently, document and gate acceptance on triage, not blind identity.
- [Modern Twisted API changes (reactor selection, `usage.Options`, klein/web serving)] → smaller surface than autobahn; covered by the same audit task.
- [Scope creep toward "improving" the suite mid-port] → non-goal stated; bug-for-bug compatibility during this change, improvements are follow-ups.

## Open Questions

- Does `testeeclient`/`testeeserver` (which test autobahn itself) still make sense pointing at modern autobahn, or should they be validated only for basic operation? (Proposed: basic operation only; they are not the conformance product.)
- Report templates: keep the legacy HTML look byte-identical or allow cosmetic drift? (Proposed: allow cosmetic drift; gate only on case outcomes/close codes.)
