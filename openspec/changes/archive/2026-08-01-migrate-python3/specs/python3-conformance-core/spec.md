# Spec: python3-conformance-core

## ADDED Requirements

### Requirement: wstest runs on Python 3
The `wstest` tool SHALL run on CPython 3.12 or newer, installed from a `pyproject.toml`-defined package with a committed `uv.lock`, with no Python 2 compatibility shims (`six`, `unittest2`, `enum34`) remaining.

#### Scenario: Tool starts and reports versions
- **WHEN** `uv run wstest -a` is executed in the project environment
- **THEN** it prints the Autobahn and AutobahnTestSuite versions and exits 0

#### Scenario: Help lists exactly the kept modes
- **WHEN** `uv run wstest --help` is executed
- **THEN** the mode list contains fuzzingserver, fuzzingclient, echoserver, echoclient, broadcastserver, broadcastclient, testeeserver, testeeclient, massconnect — and does not contain serializer, wamp, or wsperf modes

### Requirement: Fuzzing modes execute the full case suite
The fuzzingserver and fuzzingclient modes SHALL load the same test specification format as before (`fuzzingserver.json` / `fuzzingclient.json`, including `cases`, `exclude-cases`, `exclude-agent-cases`), generate the same set of ~520 test cases from `case/`, and produce HTML and JSON reports per agent.

#### Scenario: Fuzzing server runs cases against a client
- **WHEN** `wstest -m fuzzingserver` is started and a WebSocket testee client connects and runs the suite
- **THEN** all spec-selected cases execute and per-agent HTML/JSON reports are written to the configured outdir

#### Scenario: Spec file auto-generation
- **WHEN** `wstest -m fuzzingserver` is started in a directory without a spec file
- **THEN** a default `fuzzingserver.json` is auto-generated, matching the legacy default's cases and structure

### Requirement: Frame payloads are handled as bytes
All wire-facing payload paths (frame construction in fuzzing, payload literals in `case/`, masking/fragmentation helpers) SHALL use `bytes`, and binary test-case payloads SHALL be byte-identical to the Python 2 implementation's on-the-wire output.

#### Scenario: Binary echo case round-trips exactly
- **WHEN** a binary-payload case (e.g. section 1.2) runs against an echoing testee
- **THEN** the payload bytes sent and the bytes expected in the echo are identical to those produced by the frozen py2 reference for that case

#### Scenario: UTF-8 torture cases retain exact octet sequences
- **WHEN** section 6.* cases run
- **THEN** the invalid-UTF-8 octet sequences sent on the wire are byte-identical to the frozen reference's

### Requirement: Legacy and dead modes are removed
The `serializer` mode and the WAMP/wsperf modules SHALL be removed from the codebase, and modules unreachable from the kept modes SHALL be deleted rather than ported.

#### Scenario: Removed mode rejected
- **WHEN** `wstest -m serializer` is invoked
- **THEN** the tool exits with an error identifying the mode as unknown

### Requirement: CI covers the Python 3 package
The CI workflow SHALL install the py3 package with uv and run at least version/help checks and a fuzzing smoke test, without removing or altering the existing Python 2 CI job or the frozen Docker image build.

#### Scenario: CI green on py3 job
- **WHEN** the CI workflow runs on a push
- **THEN** a py3 job installs the package via uv and its checks pass, and the pre-existing py2 job still runs unchanged
