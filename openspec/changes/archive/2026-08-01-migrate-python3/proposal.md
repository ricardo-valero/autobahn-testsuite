# Proposal: migrate-python3

## Why

The testsuite runs on Python 2.7 (EOL January 2020) atop a frozen 2019-era stack (Twisted 19.10, autobahn 0.10.9, cryptography 3.3.2, OpenSSL 1.1), which makes every environment increasingly hard to stand up: CPython 2.7 must be built from source in CI, macOS dev environments need insecure-flagged OpenSSL 1.1 (see `add-nix-dev-env`), and nixpkgs is sunsetting the platforms this stack builds on. This fork deliberately diverges from upstream's freeze policy: modernize the runtime to Python 3 + uv while the frozen Docker image remains the historical conformance reference.

## What Changes

- Port the conformance core (~14,200 LOC: 28 modules + 143 test-case files in `case/`) from Python 2.7 to Python 3 (target: 3.12+), on modern Twisted and modern autobahn.
- **BREAKING**: Drop the `serializer` mode (imports `autobahn.wamp.test.test_serializer`, removed in modern autobahn) and delete the already-disabled WAMP/wsperf modules (`wamp*`, `wsperf*`, `wampfuzzing`, `wamptestserver`, `wamptestee`) — they are commented out of `wstest.py`/`__init__.py` today and unreachable.
- Kept modes: `fuzzingserver`, `fuzzingclient`, `echoserver`, `echoclient`, `broadcastserver`, `broadcastclient`, `testeeserver`, `testeeclient`, `massconnect`.
- **BREAKING**: Replace `setup.py` + `requirements.txt` pins with `pyproject.toml` managed by uv (lockfile committed).
- Build a differential-validation harness: run the frozen Docker fuzzingserver and the ported py3 fuzzingserver against the same testee client and diff the generated reports — behavioral equivalence is the acceptance gate, since the suite's value is its stable, known behavior.
- Update CI to test the py3 package; the py2 CPython-from-source CI job and the frozen Docker image remain untouched.

## Capabilities

### New Capabilities

- `python3-conformance-core`: The `wstest` conformance tool (fuzzing/echo/testee/broadcast/massconnect modes, ~520 test cases, HTML/JSON reports) running on Python 3 with modern Twisted/autobahn.
- `differential-validation`: Harness proving the py3 port produces equivalent test behavior and reports to the frozen Python 2 Docker reference.

### Modified Capabilities

<!-- none: nix-dev-environment keeps providing the py2 toolchain during the transition; simplifying it is a follow-up change after the port is validated -->

## Impact

- **Code**: all of `autobahntestsuite/autobahntestsuite/` (py2→py3 syntax, and pervasively the bytes/str boundary — a WebSocket fuzzer manipulates raw frame bytes, so py2 `str` payload handling must become explicit `bytes` throughout `fuzzing.py` and the 143 case files).
- **Dependencies**: autobahn 0.10.9 → modern autobahn (pinned); Twisted 19.10 → modern Twisted; klein/jinja2/markupsafe/werkzeug unpinned to current; `unittest2`, `six`, `enum34`-era shims removed.
- **Removed**: `serializer.py`, `wamptestee.py`, `wamptestserver.py`, `wampfuzzing.py`, `wsperfcontrol.py`, `wsperfmaster.py`, `testdb.py`/`testrun.py`/`rinterfaces.py` if confirmed dead, `setup.py`, `requirements.txt`.
- **Unchanged**: `docker/` frozen image, py2 CI job, published PyPI history; the py2 stack stays runnable via the existing dev env until validation passes.
