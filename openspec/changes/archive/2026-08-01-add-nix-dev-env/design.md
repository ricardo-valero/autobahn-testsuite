# Design: add-nix-dev-env

## Context

The repo is a fork of crossbario/autobahn-testsuite, intentionally frozen on Python 2.7 (README "Legacy Compatibility Note", `docker/Dockerfile` "DO NOT UPGRADE"). Its dev bootstrap is Ubuntu-specific (`justfile` uses `apt-get` and builds CPython 2.7 from source), which does not work on macOS. The `justfile` already uses `uv` for a Python 3 tooling venv (Sphinx, twine), so the host-side tool expectations are: `just`, `uv`, Docker, plus standard shell utilities.

`python27` was removed from nixpkgs years ago, so a flake cannot simply provide CPython 2.7 from the standard package set.

## Goals / Non-Goals

**Goals:**
- One-command reproducible dev shell on macOS (aarch64/x86_64-darwin) and Linux via `flake.nix` + direnv.
- Provide the host-side tools the existing `justfile` workflows need: `just`, `uv`, and Docker CLI support for running the frozen testsuite image.
- Zero disruption to existing workflows: CI, Docker image, and Ubuntu bootstrap recipes keep working unchanged.

**Non-Goals:**
- Providing a native Python 2.7 runtime through Nix (see Decision 2).
- Porting the testsuite to Python 3 (separate, contested change — repo policy is to stay frozen).
- Changing CI to use Nix.

## Decisions

### Decision 1: flake.nix with nixpkgs (unstable) + flake-utils-style per-system devShell

Standard flake layout: `inputs.nixpkgs` pinned via `flake.lock`, a `devShells.default` for each supported system. Packages: `just`, `uv`, `git`, and optionally `colima`/`docker-client` hints in shellHook rather than as hard dependencies (Docker Desktop/Colima installation is machine-level, not project-level, on macOS).

*Alternative considered*: devenv/devbox — heavier abstractions; a plain flake is enough for three tools and keeps the file self-explanatory.

### Decision 2: Native CPython 2.7.18 via `cachix/nixpkgs-python`, Docker demoted to reference fallback

The flake takes `cachix/nixpkgs-python` as an input and puts CPython 2.7.18 (`python2`) on the dev-shell PATH. Verified: the flake ships 2.7.18 for x86_64-darwin (and Linux systems). This is consistent with upstream practice: CI already builds CPython 2.7.18 from source on Ubuntu; the "frozen" policy applies to the published PyPy Docker image, not dev environments.

**Implementation finding (supersedes the original wheel assumption):** the nixpkgs-python CPython is built UCS-4 (`cp27mu` ABI), so PyPI's `cp27m` macOS binary wheels (e.g. cryptography 3.3.2) do not match and pip falls back to source builds. The dev shell therefore also provides `pkg-config`, `libffi`, and `openssl_1_1` (1.1.1w — the same version the frozen Docker image uses; allowed via `permittedInsecurePackages`, which requires `import nixpkgs { config = ...; }` instead of `legacyPackages`). The shellHook exports `PKG_CONFIG_PATH`/`CFLAGS`/`LDFLAGS` pointing at these so cffi and cryptography compile cleanly. Note Hydra does not cache insecure-flagged packages, so OpenSSL 1.1 compiles locally on first entry.

The venv is created with a Python 3 `virtualenv<20.22` (the last series able to target py2.7, seeds pip 20.3.4 automatically), e.g. `uvx 'virtualenv<20.22' -p python2 .venvs/cpy27` — this avoids `get-pip.py` trying to write into the read-only Nix store.

*Alternatives considered*:
- Docker-only — safest w.r.t. behavioral fidelity, but means no local iteration without a container runtime; kept as the reference/CI-parity path (`just docker-test`), not the dev default.
- `pkgs.pypy2` from nixpkgs — packaged for all four platforms and matches the Docker image's interpreter, but there are no PyPy2 wheels for `cryptography`, forcing a source build against insecure-flagged `openssl_1_1`. More faithful, much more fragile.

### Decision 2a: Docker remains the conformance reference

Native runs are for development iteration. The frozen `pypy:2-7-bullseye` image remains the blessed reference for published conformance reports, and nixpkgs has announced x86_64-darwin sunset after release 26.05 — so the Docker path is retained and documented, not removed.

### Decision 3: `.envrc` contains only `use flake`

Direnv activation via the standard one-liner. No `dotenv`, no custom layout. Contributors without direnv can still run `nix develop` manually.

### Decision 4: gitignore additions kept minimal

Add `.direnv/` to the existing root `.gitignore`. `flake.lock` is committed (reproducibility is the point). No other ignore entries needed — `.uv-cache` is CI-workspace-scoped, not local.

## Risks / Trade-offs

- [Contributors without Nix installed get nothing from `.envrc`] → README/CHANGELOG note; the flake is additive and the old Ubuntu path still works.
- [Nix flags OpenSSL 1.1 as insecure (EOL since 2023)] → scoped to the dev shell only, mirrors the frozen Docker image's OpenSSL 1.1.1w, and is explicitly permitted in the flake with a comment explaining why.
- [`uv` from nixpkgs may lag the latest release] → acceptable; the `justfile` uses stable `uv venv`/`uv run --script` interfaces only.
- [C extensions in `autobahn[accelerate]` (wsaccel, ujson) may fail to compile under modern clang (implicit-function-declaration errors)] → set `CFLAGS=-Wno-error=implicit-function-declaration` in the shellHook, or install without the `accelerate` extra — it is a performance optimization, not a functional dependency.
- [Native runs could drift behaviorally from the frozen PyPy reference image] → native env is for development iteration only; conformance reports for publication still come from `just docker-test` (Decision 2a).
- [nixpkgs is sunsetting x86_64-darwin after release 26.05] → flake.lock pins a working revision; Docker path remains as the durable fallback.
- [`cachix/nixpkgs-python` is a third-party flake input] → widely used (Cachix-maintained, binary cache available); pinned via flake.lock like everything else.
- [nixpkgs-unstable drift when the lock is updated] → `flake.lock` pins exact revisions; updates are explicit (`nix flake update`).

## Open Questions

- None blocking. (The `justfile`'s `install-python2` recipe already skips its apt path when `command -v python2` succeeds, so the flake-provided interpreter slots in; only venv creation needs the `virtualenv<20.22` route instead of `get-pip.py`.)
