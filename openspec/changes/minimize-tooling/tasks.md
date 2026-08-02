# Tasks: minimize-tooling

## 1. Preserve the frozen py2 artifacts

- [x] 1.1 Tag the last py2-capable commit (pre-migration) as `v25.10.1-py2` and push the tag, so the frozen Dockerfile + py2 source stay retrievable
- [x] 1.2 Confirm `crossbario/autobahn-testsuite:25.10.1` is present on Docker Hub (immutable frozen reference); note it in `test/differential/README.md`

## 2. Dependencies: latest, unpinned

- [x] 2.1 Remove `cbor2<6` and `cryptography<49` from `pyproject.toml` `constraint-dependencies`; bump the autobahn/Twisted floors to current; re-run `uv lock` and `uv sync`
- [x] 2.2 Verify the suite still imports and the CI smoke test passes on the new resolution (`uv run python test/differential/smoke_py3.py`)
- [x] 2.3 Move Sphinx/docs pins from `requirements-dev.txt` into a `[dependency-groups] docs` entry in `pyproject.toml`

## 3. Flake overhaul

- [x] 3.1 Rewrite `flake.nix` in the `flakeExposed` + `genAttrs` + `builtins.attrValues` style; dev shell packages = `just`, `uv`, `python3` (with `uv`), `rustc`, `cargo`, `pkg-config`, `nixd`, `alejandra`
- [x] 3.2 Remove the `nixpkgs-python` input, `python2`, `openssl_1_1`, the `permittedInsecurePackages` config, and the py2 `CFLAGS`/`LDFLAGS`/venv shellHook wiring
- [x] 3.3 Keep the flake to dev-env only — no app/package derivation, no uv2nix; optionally set `formatter` to `alejandra`
- [x] 3.4 `nix flake check` passes with no insecure-package permission; `nix develop -c uv run wstest -a` prints versions

## 4. Slim the justfile (keep just)

- [x] 4.1 Delete the py2 recipes (`install-python2*`, `create-venv`, `install*`, py2 `test-*`) and the docker recipes (`docker-build`, `docker-test`, `publish-to-dockerhub`)
- [x] 4.2 Add thin py3 recipes wrapping uv/nix: `dev` (nix develop), `run` (uv run wstest), `build` (uv build), `publish` (uv publish), `check` (nix flake check + ty), `docs` (sphinx via docs group)
- [x] 4.3 `just --list` shows only the current recipes and each runs

## 5. Remove dead py2 packaging + docker

- [x] 5.1 Delete `docker/`, `setup.py`, `MANIFEST.in`, `requirements.txt`, `requirements-dev.txt`, `autobahntestsuite/Makefile`
- [x] 5.2 Confirm `uv build` still produces the wheel/sdist (package metadata fully sourced from `pyproject.toml`) and `uv run wstest -a` works

## 6. Differential reference without docker (optional, per design Decision 6)

- [ ] 6.1 (deferred — needs a Docker host; optional) Capture the frozen reference reports once from the published image and commit them as fixtures under `test/differential/reference/`; point `normalize_reports.py` at the fixtures so validation needs no container runtime

## 7. Docs + CI

- [x] 7.1 Update `README.md`: install/run story is `nix run` / `uvx` / `pip`; keep a short "test a non-Python implementation" note using the published `:25.10.1` image; mark the frozen image as the historical reference
- [x] 7.2 Update `.github/workflows/main.yml`: add a `nix flake check` guard for the dev shell; ensure the docs job no longer relies on removed files
- [x] 7.3 Record the follow-up trigger: when the dev machine moves to Apple Silicon, switch the flake's nixpkgs input from `nixpkgs-26.05-darwin` back to `nixpkgs-unstable`
