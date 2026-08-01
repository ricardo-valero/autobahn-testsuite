# Audit: autobahn API surface (0.10.9 → 26.7.1)

Verified by introspection against autobahn 26.7.1 / Twisted 26.4.0 / CPython 3.12.13
(96 automated symbol checks + source inspection). Inventory extracted from
`fuzzing.py`, `testee.py`, `echo.py`, `broadcast.py`, `massconnect.py`, `util.py`,
`wstest.py`, `case/case.py`, and sampled case files.

## Verdict: migrate to modern autobahn, no vendoring required

89/96 checks pass unchanged. The frame-level fuzzing surface — the highest-risk
area — survives intact: `sendFrame(opcode, payload, fin, rsv, mask, payload_len,
chopsize, sync)` has the **identical signature** in 26.7.1, and every protocol
flag the reports read (`closedByMe`, `failedByMe`, `droppedByMe`, `wasClean`,
`wasNotCleanReason`, `was*Timeout`, `local/remoteCloseCode/Reason`,
`http_request_data`, `http_response_data`) still exists. All close-status/state
constants, `Utf8Validator`, `XorMaskerNull`, `utcnow`, `newid`, `connectWS`,
`listenWS`, and the streaming API (`beginMessage`/`beginMessageFrame`/
`sendMessageFrameData`/`endMessage`) are unchanged.

## Required adaptations (complete list)

| # | Symbol | Change | Adaptation |
|---|--------|--------|------------|
| 1 | `failConnection()` | renamed → `_fail_connection(code, reason)` | single call site `fuzzing.py:257`; call the underscore method (add local alias with comment) |
| 2 | `PerMessageSnappy*` (4 classes) | **removed** | delete snappy branches in `testee.py` compression handling; deflate + bzip2 survive |
| 3 | Factory ctor kwargs `debug=`, `debugCodePaths=` | removed (autobahn ≥0.17, txaio logging era) | drop the kwargs at all factory instantiations; remove `factory.debug`/`debugCodePaths` attributes |
| 4 | Protocol/factory `self.debug` attribute | removed | replace debug-gated prints with a module-level logger (or a local `self.debug` set by our own factories) |
| 5 | `setSessionParameters(url, protocols, server, origin, useragent)` | now `(url, protocols, server, headers, externalPort)` | pass `origin`/`useragent` via `headers` dict where actually needed (fuzzing client `useragent`) |
| 6 | `connectionWasOpen` | never was autobahn API — defined in `fuzzing.py:89,282` | no action |
| 7 | `perMessageCompressionOffers` | still exists, on **client** factory only (as before) | no action |

Everything else: no action.

## Non-autobahn py3 adaptations found during audit

- `wstest.py` uses `pkg_resources` → `importlib.metadata`.
- All intra-package imports are py2 implicit-relative (`import fuzzing`) → absolute (`from autobahntestsuite import fuzzing`).
- `twisted.python.log` → still present but legacy; keep for now (bug-for-bug), modernize later.

## Module reachability verdicts (task 1.2)

| Module | Verdict | Reason |
|--------|---------|--------|
| `serializer.py` | DELETE | imports `autobahn.wamp.test` (gone); mode dropped per proposal |
| `wamptestee.py`, `wamptestserver.py`, `wampfuzzing.py` | DELETE | wamp1 API (gone); already commented out of wstest/__init__ |
| `wsperfcontrol.py`, `wsperfmaster.py` | DELETE | wamp1 + dead modes |
| `testdb.py`, `testrun.py`, `rinterfaces.py` | DELETE | only imported by each other and `wampfuzzing.py` |
| `interfaces.py` | KEEP (trim) | `report.py:423` uses `IReportGenerator`; delete the ITestDb/ITestRun/ITestRunner interfaces |
| everything else | KEEP + port | reachable from the 9 kept modes |

**Dependency fallout**: `klein` and `werkzeug` are imported only by `wampfuzzing.py` → dropped entirely. `unittest2`, `six`, `enum34`-era shims → dropped.

## Shim/vendor decisions (task 1.3)

- **No vendoring.** All 5 real adaptations are call-site edits or trivial local aliases; nothing removed from modern autobahn is load-bearing for frame fuzzing.
- **Dependency packaging note for task 2.1**: autobahn 26.7.1 hard-depends on `cbor2`, which has no x86_64-macOS wheel and needs Rust to build. Options: (a) add `rustc`/`cargo` to the flake dev shell, (b) pin an autobahn version without the cbor2 hard dep, (c) accept that x86_64-mac contributors need rustup. Decide in task 2.1; CI (Linux) has cbor2 wheels and is unaffected. Likewise pin `cryptography` to a wheel-available version on this platform (48.0.1 verified).
- **Behavioral watch-item for differential runs**: permessage-deflate internals have 10 years of drift; cases 12.*/13.* are the most likely source of triage entries (already flagged in design Risks).
