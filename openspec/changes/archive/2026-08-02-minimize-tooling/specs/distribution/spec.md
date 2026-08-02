# Spec: distribution

## ADDED Requirements

### Requirement: nix and uv remain decoupled
The flake SHALL provide only the development environment (toolchain + dev shell) and SHALL NOT contain a Python application/package derivation or a `nix run` app for `wstest`. The integration surface between Nix and uv is limited to Nix placing `uv` on PATH.

#### Scenario: No app/package outputs in the flake
- **WHEN** `nix flake show` is run
- **THEN** the flake exposes `devShells` (and optionally `formatter`) but no `apps.*.wstest` or `packages.*` app derivation

#### Scenario: Running the suite from the dev shell
- **WHEN** a contributor is in the dev shell and runs `uv run wstest -m fuzzingserver`
- **THEN** the fuzzing server starts on port 9001 with no nix↔python bridge involved

### Requirement: Python-native distribution via PyPI
The package SHALL remain installable and runnable through standard Python tooling from `pyproject.toml`.

#### Scenario: Ephemeral run with uvx
- **WHEN** a user runs `uvx autobahntestsuite wstest -a`
- **THEN** the Autobahn and AutobahnTestSuite versions print without a persistent install

#### Scenario: pip install exposes wstest
- **WHEN** a user runs `pip install autobahntestsuite` into a Python 3.12+ environment
- **THEN** a `wstest` console script is available

### Requirement: No Docker image is built from master
Master SHALL NOT contain a Dockerfile or docker build/publish tasks. The frozen Python 2 reference image remains available externally as the immutable published `crossbario/autobahn-testsuite:25.10.1` and via the `v25.10.1-py2` git tag.

#### Scenario: No docker plumbing on master
- **WHEN** the repository tree on master is inspected
- **THEN** there is no `docker/` directory and no docker build/publish recipe

#### Scenario: Frozen reference still reachable
- **WHEN** a user needs the historical py2 behavior
- **THEN** `docker run crossbario/autobahn-testsuite:25.10.1` (published, immutable) and the `v25.10.1-py2` tag both remain usable
