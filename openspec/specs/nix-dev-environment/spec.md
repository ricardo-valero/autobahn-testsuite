# Spec: nix-dev-environment

## Requirements

### Requirement: Reproducible dev shell via Nix flake
The repository SHALL provide a `flake.nix` at the repo root that defines a default dev shell (`devShells.default`) for Linux and macOS systems (x86_64-linux, aarch64-linux, x86_64-darwin, aarch64-darwin) containing at minimum `just`, `uv`, and CPython 2.7.18 (as `python2`, sourced from the `cachix/nixpkgs-python` flake input). The flake SHALL commit its `flake.lock` so the environment is pinned and reproducible.

#### Scenario: Developer enters the dev shell manually
- **WHEN** a contributor with Nix (flakes enabled) runs `nix develop` at the repo root
- **THEN** a shell opens where `just --version`, `uv --version`, and `python2 --version` (reporting 2.7.18) all succeed

#### Scenario: Flake evaluates cleanly
- **WHEN** `nix flake check` is run at the repo root
- **THEN** it completes without evaluation errors

### Requirement: Automatic activation via direnv
The repository SHALL provide a `.envrc` at the repo root containing `use flake`, so that contributors with direnv installed get the dev shell automatically on entering the directory.

#### Scenario: direnv activates the environment
- **WHEN** a contributor with direnv runs `direnv allow` in the repo root
- **THEN** subsequent shells in that directory have `just` and `uv` on PATH without running `nix develop` manually

### Requirement: Local environment artifacts are ignored by git
The repository's `.gitignore` SHALL exclude the `.direnv/` directory so direnv's local cache is never committed.

#### Scenario: direnv cache not tracked
- **WHEN** direnv has populated `.direnv/` and `git status` is run
- **THEN** `.direnv/` does not appear as an untracked path

### Requirement: Native testsuite execution without Docker
The dev shell SHALL support installing and running the testsuite natively: with the flake-provided `python2`, a virtual environment created via a Python 3 `virtualenv<20.22` (e.g. `uvx 'virtualenv<20.22' -p python2`) SHALL be able to `pip install` the pinned `autobahntestsuite/requirements.txt` and the package itself, yielding a working `wstest` command. The shellHook SHALL set any compiler flags needed for the pinned C extensions to build under modern clang (e.g. `-Wno-error=implicit-function-declaration`).

#### Scenario: wstest runs natively
- **WHEN** a contributor creates the py2 venv from the dev shell and installs the pinned requirements plus the package
- **THEN** `wstest --help` and `wstest -a` succeed without Docker

#### Scenario: Fuzzing server starts natively
- **WHEN** the contributor runs `wstest -m fuzzingserver` from the venv
- **THEN** the fuzzing server starts and listens on port 9001 (and the embedded web server on 8080)

### Requirement: Docker image remains the conformance reference
The frozen Docker image (`docker/`) SHALL remain the reference environment for published conformance reports. The dev shell SHALL NOT modify or replace the Docker workflow, and existing CI/Ubuntu bootstrap recipes SHALL behave exactly as before this change.

#### Scenario: Existing workflows unaffected
- **WHEN** the existing CI workflow or Ubuntu `justfile` bootstrap recipes run on a machine without Nix
- **THEN** they behave exactly as before this change
