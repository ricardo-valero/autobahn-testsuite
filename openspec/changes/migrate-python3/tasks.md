# Tasks: migrate-python3

## 1. Audit (before any porting)

- [x] 1.1 Inventory every autobahn symbol the testsuite imports or overrides (imports across all modules; overridden methods of WebSocket protocol/factory classes in `fuzzing.py`, `testee.py`, `echo.py`, `broadcast.py`, `massconnect.py`) and map each to the modern autobahn API — produce `openspec/changes/migrate-python3/audit.md` with per-symbol status: unchanged / renamed / signature-changed / removed
- [x] 1.2 Audit `testdb.py`, `testrun.py`, `rinterfaces.py`, `interfaces.py`, `wsperfmaster.py` reachability from the 9 kept modes; list keep/delete verdicts in audit.md
- [x] 1.3 Decide per-symbol shims vs vendoring for anything removed/incompatible (design Decision 1 escape hatch); record in audit.md

## 2. Packaging scaffold

- [x] 2.1 Create `pyproject.toml` (PEP 621, py3.12 floor, modern autobahn + Twisted + jinja2 + klein-or-replacement per audit) with `wstest` entry point; commit `uv.lock`
- [x] 2.2 Add `ty` (Astral type checker) to dev deps and a `ty check` just recipe; run it as an advisory gate after the port phases (autobahn 26.x ships type annotations, so ty flags str-vs-bytes violations at sendFrame/sendMessage call sites)
- [x] 2.3 Add py3 recipes to the justfile (`install-py3`, `test-wstest-py3`) alongside the existing py2 recipes, using uv
- [x] 2.4 Delete dead modules per audit verdicts (`serializer.py`, `wamptestee.py`, `wamptestserver.py`, `wampfuzzing.py`, `wsperfcontrol.py`, plus any 1.2 deletions) and remove their mode wiring from `wstest.py`

## 3. Core port (non-case modules)

- [x] 3.1 Port `wstest.py`, `choosereactor.py`, `spectemplate.py`, `util.py`, `caseset.py` (CLI, options, spec loading) to py3
- [x] 3.2 Port `fuzzing.py` to py3 with explicit bytes discipline on all frame-construction and payload paths; adapt overridden autobahn hooks per audit map
- [x] 3.3 Port `testee.py`, `echo.py`, `broadcast.py`, `massconnect.py` to py3
- [x] 3.4 Port `report.py` and the jinja2 templates (modern jinja2 API; cosmetic drift allowed, outcomes/close-code fields unchanged)
- [x] 3.5 `uv run wstest -a` and `--help` succeed; `--help` lists exactly the 9 kept modes

## 4. Case files port (143 files)

- [x] 4.1 Define the mechanical rewrite rules for `case/` (payload literals to `b""`, `chr()` to `bytes([...])`, concat/join/slicing on payloads as bytes, `%`-format on payloads eliminated) and encode them in a one-off rewrite script committed under `test/`
- [x] 4.2 Apply the rules across `case/`, then hand-audit the byte-sensitive sections (1.*, 4.*, 5.*, 6.*) against the py2 originals
- [x] 4.3 Smoke: `wstest -m fuzzingserver` starts, auto-generates the default spec, and runs a subset (1.*, 2.*) against a py3 echo client without exceptions

## 5. Differential validation harness

- [x] 5.1 Build `test/differential/`: scripts to launch reference (Docker) and py3 fuzzingservers with identical specs, drive `testee_client_aio.py` against each, and collect reports
- [x] 5.2 Implement the report normalizer (strip timestamps/durations/versions/ordering only) and diff tool with non-zero exit on untriaged differences; verify same-implementation-twice yields an empty diff
- [ ] 5.3 (follow-up, needs Docker) Implement wire-level frame capture and byte-for-byte comparison for the sampled byte-sensitive cases (masking, fragmentation, section 6)
- [x] 5.4 Create the triage file format and document the triage workflow in `test/differential/README.md`

## 6. Validation runs

- [ ] 6.1 (follow-up, needs Docker) Full differential run (all cases incl. 9.*, 12.*, 13.*) fuzzingserver-vs-reference; fix port bugs or triage environment artifacts until the harness exits zero
- [ ] 6.2 (follow-up, needs Docker) Differential run for fuzzingclient mode against a reference testee server
- [ ] 6.3 (follow-up, needs Docker) Wire-level spot-check run passes for the sampled sections
- [x] 6.4 Basic-operation checks for echo/broadcast/testee/massconnect modes (start, connect, exchange, clean close)

## 7. CI, docs, cleanup

- [x] 7.1 Add a py3 CI job (uv install, `wstest -a`, fuzzing smoke test) to `.github/workflows/main.yml` without modifying the existing py2 job or Docker build
- [x] 7.2 Keep `setup.py`/`requirements.txt` (still consumed by the frozen py2 CI job); py3 uses pyproject.toml. Full removal deferred to the py2-retirement follow-up from the py3 path (keep them only if the py2 CI job still consumes them; note the follow-up to retire py2 entirely)
- [x] 7.3 Update README: py3 quickstart with uv, kept-modes list, differential-validation note; mark the Legacy Compatibility Note as applying to the frozen Docker reference
- [x] 7.4 Update the flake dev shell with python3.12+ (keep the py2 toolchain until the py2 retirement follow-up)
