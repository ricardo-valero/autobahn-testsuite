# Tasks: add-nix-dev-env

## 1. Flake

- [x] 1.1 Create `flake.nix` with inputs `nixpkgs` and `cachix/nixpkgs-python`, and `devShells.default` for x86_64-linux, aarch64-linux, x86_64-darwin, aarch64-darwin containing `just`, `uv`, and CPython 2.7.18 (`python2` on PATH)
- [x] 1.2 Add a shellHook that sets `CFLAGS=-Wno-error=implicit-function-declaration` (for wsaccel/ujson builds under modern clang) and prints a short note: native py2 venv for dev iteration, Docker image for reference conformance runs
- [x] 1.3 Run `nix flake lock` to generate `flake.lock`, and verify `nix flake check` passes (note: nixpkgs pinned to `nixpkgs-26.05-darwin` — unstable/26.11 dropped x86_64-darwin entirely)

## 2. Direnv integration

- [x] 2.1 Create `.envrc` containing `use flake`
- [x] 2.2 Add `.direnv/` to the root `.gitignore` (also added `.venvs/` for the native py2 venv)
- [x] 2.3 Run `direnv allow` and verify `just --version`, `uv --version`, and `python2 --version` (2.7.18) resolve from the flake environment

## 3. Native testsuite venv

- [x] 3.1 Create the py2 venv from the dev shell: `uvx 'virtualenv<20.22' -p python2 .venvs/cpy27` (avoids `get-pip.py` writing into the read-only Nix store; seeds pip 20.3.4)
- [x] 3.2 Install pinned deps and the package: `.venvs/cpy27/bin/pip install -r autobahntestsuite/requirements.txt` then `pip install ./autobahntestsuite` — confirm cryptography 3.3.2 installs from a binary wheel (no OpenSSL 1.1 source build); if the `accelerate` C extensions fail to build, fall back to installing without that extra
- [x] 3.3 Verify `wstest --help` and `wstest -a` succeed natively
- [x] 3.4 Smoke-test `wstest -m fuzzingserver` — listens on 9001, web UI on 8080

## 4. Verification and docs

- [x] 4.1 Verify `nix develop --command just --version` works from a clean shell (no direnv)
- [x] 4.2 Confirm existing recipes are unaffected: `just --list` runs, and no tracked files changed except the intended ones
- [x] 4.3 Add a short "Development environment (Nix)" note to README or CHANGELOG covering `nix develop` / direnv usage, the native py2 venv recipe, and that Docker remains the conformance reference
