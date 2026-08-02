# Spec: nix-dev-environment (delta)

## MODIFIED Requirements

### Requirement: Reproducible dev shell via Nix flake
The repository SHALL provide a `flake.nix` at the repo root that defines a default dev shell (`devShells.<system>.default`) for the systems in `nixpkgs.lib.systems.flakeExposed`, containing at minimum `just`, `uv`, CPython 3 (`python3`, matching the `pyproject.toml` floor), `rustc` and `cargo` (for source-building transitive Rust deps where wheels are absent), and the Nix authoring tools `nixd` and `alejandra`. The flake SHALL NOT contain a Python 2 interpreter, the `nixpkgs-python` input, or any `permittedInsecurePackages` entry. The flake SHALL commit its `flake.lock` so the environment is pinned and reproducible.

#### Scenario: Developer enters the dev shell manually
- **WHEN** a contributor with Nix (flakes enabled) runs `nix develop` at the repo root
- **THEN** a shell opens where `just --version`, `uv --version`, and `python3 --version` (reporting the pyproject floor or newer) all succeed, and no Python 2 interpreter is on PATH

#### Scenario: Flake evaluates cleanly with no insecure packages
- **WHEN** `nix flake check` is run at the repo root
- **THEN** it completes without evaluation errors and without requiring any insecure-package permission

## REMOVED Requirements

### Requirement: Native testsuite execution without Docker
**Reason:** This requirement described running the *Python 2* suite via a `virtualenv<20.22` venv, the frozen `requirements.txt`, and clang workaround flags. The suite is now Python 3; that entire py2 local-execution path (and its `openssl_1_1`/`pkg-config`/`libffi` support) no longer exists.
**Migration:** Run the Python 3 suite with `uv run wstest` / `nix run <repo>#wstest`, or install from PyPI with `uvx autobahntestsuite`. See the `distribution` capability.
