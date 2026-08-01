# Proposal: add-nix-dev-env

## Why

The repo's bootstrap tooling (`justfile` recipes `install-python2`, `install-python2-deps`) is Debian/Ubuntu-only — it uses `apt-get`, `sudo ldconfig`, and builds CPython 2.7 from source. On macOS (the current dev machine) there is no working path to a local dev environment at all. A Nix flake with direnv gives every contributor a reproducible, cross-platform shell with the host-side tools the repo already expects (`just`, `uv`, Docker tooling) without touching the intentionally frozen Python 2.7 runtime.

## What Changes

- Add `flake.nix` providing a dev shell with the tools the existing workflows need: `just` (build system), `uv` (already used by the `tools-venv` recipe for Python 3 docs/publishing tooling), and **CPython 2.7.18** via the `cachix/nixpkgs-python` flake input — enabling native (Docker-free) execution of `wstest` on macOS and Linux.
- Add `.envrc` with `use flake` so direnv activates the environment automatically on `cd`.
- Add `.direnv/` (and flake-related transients) to `.gitignore`.
- The testsuite is **not** ported to Python 3 and the frozen `pypy:2-7-bullseye` Docker image remains the reference for published conformance reports; the native path is for development iteration. This is consistent with upstream practice — CI already builds CPython 2.7.18 outside Docker.

## Capabilities

### New Capabilities

- `nix-dev-environment`: Reproducible development shell (flake.nix + .envrc/direnv) providing host-side tooling (`just`, `uv`, Docker-based testsuite execution support) on macOS and Linux.

### Modified Capabilities

<!-- none — no existing specs in openspec/specs/; the frozen Python 2 runtime behavior is unchanged -->

## Impact

- **New files**: `flake.nix`, `flake.lock`, `.envrc`.
- **Modified files**: `.gitignore` (add `.direnv/`).
- **Unchanged**: `justfile` recipes, `docker/` image, `autobahntestsuite/` package, CI workflow — the flake is additive; existing Ubuntu CI bootstrap keeps working.
- **Dependencies**: contributors need Nix (with flakes enabled) and direnv installed; Docker (or Colima on macOS) for running the actual testsuite.
