# Proposal: minimize-tooling

## Why

Now that master is Python 3, the tooling built up around the frozen Python 2 suite is dead weight and, in several places, actively broken. `just docker-build` still targets `pypy:2-7-bullseye` and a `-py2-none-any.whl` that the py3 build no longer produces; the flake still carries a whole Python 2 toolchain (`nixpkgs-python`, `python2`, the security-flagged `openssl_1_1`) whose only job was running the py2 suite locally; and dependencies are pinned backward (`cbor2<6`, `cryptography<49`) solely to accommodate x86_64-macOS wheels on a platform nixpkgs sunsets after 26.05. Roughly half the `justfile` recipes (py2 build/venv, docker build/push) orchestrate rituals we are deleting.

Goal: a **minimal** repo built on `uv` + `nix`, with `just` retained as the discoverable command menu wrapping them, distributed to end users via `nix run` and `uvx`, on the latest dependencies.

## What Changes

- **Remove Docker from master.** Delete `docker/` (Dockerfile, config, Makefile, versions.sh) and the `docker-build`/`docker-test`/`publish-to-dockerhub` recipes. **BREAKING** for anyone building the image from source. The already-published, immutable `crossbario/autobahn-testsuite:25.10.1` image stays on Docker Hub as the frozen py2 conformance reference; a git tag `v25.10.1-py2` preserves the last py2 source + Dockerfile.
- **Add `nix run` distribution.** Expose `apps.<system>.wstest` so `nix run <repo>#wstest -- -m fuzzingserver` runs the suite with zero install. `uvx autobahntestsuite` / `pip install` remain the Python-native channel.
- **Slim the `justfile` (keep `just`).** Remove the py2 build/venv and docker recipes; keep `just` as the discoverable command menu, with recipes that wrap the `uv`/`nix` verbs (`just dev`, `just run`, `just build`, `just publish`, `just check`). **BREAKING** only for callers of the removed py2/docker recipes.
- **Drop the dependency pins.** Remove `cbor2<6` and `cryptography<49` (latest everywhere); add `rustc`/`cargo` to the dev shell so the current Intel Mac can source-build those two transitive deps until the move to Apple Silicon makes wheels available.
- **Overhaul the flake.** Adopt `nixpkgs.lib.systems.flakeExposed` + `genAttrs`, `builtins.attrValues`-over-attrset package sets, and `python3.withPackages`; add `nixd` and `alejandra`. **Shed the entire py2 toolchain** (`nixpkgs-python` input, `python2`, `openssl_1_1`, py2 `pkg-config`/`libffi` wiring, the `virtualenv<20.22` venv workflow) — there is no py2 code left to run locally, so this also removes the insecure-OpenSSL permission.
- **Delete dead py2 packaging files:** `setup.py`, `MANIFEST.in`, `requirements.txt`, `autobahntestsuite/Makefile`. Move the Sphinx/docs pins from `requirements-dev.txt` into a `[dependency-groups] docs` entry in `pyproject.toml`.
- Update README so the install story is `nix run` / `uvx`, and note the frozen published image as the historical reference.

## Capabilities

### New Capabilities

- `distribution`: How end users obtain and run `wstest` — `nix run` (flake app), `uvx`/`pip` (PyPI) — with Docker removed from master and the published py2 image retained as the immutable frozen reference.

### Modified Capabilities

- `nix-dev-environment`: The flake dev shell moves from a Python 2 toolchain to a minimal Python 3 one (just, uv, python3, rust, nixd, alejandra), drops the `nixpkgs-python`/`openssl_1_1` machinery and the py2 venv workflow, and adopts the `flakeExposed`/`genAttrs`/`attrValues` authoring style.

## Impact

- **Removed files:** `docker/`, `setup.py`, `MANIFEST.in`, `requirements.txt`, `requirements-dev.txt`, `autobahntestsuite/Makefile`.
- **Modified files:** `justfile` (slim to py3/uv/nix recipes), `flake.nix`, `flake.lock`, `pyproject.toml` (drop pins, add docs group, wire the `wstest` app), `.github/workflows/main.yml` (docs job), `README.md`.
- **Preserved externally:** the immutable `crossbario/autobahn-testsuite:25.10.1` Docker Hub image and a new `v25.10.1-py2` git tag.
- **Dependencies:** contributors need `nix` (+ optional `direnv`); Docker is no longer required for anything on master. The differential-validation harness still `docker run`s the *published* frozen image to capture reference reports (or uses committed report fixtures — see design).
