# Design: minimize-tooling

## Context

The `migrate-python3` change modernized the *code*; this change sheds the *scaffolding* that existed only for the Python 2 era. Three legacy anchors remain on master, all now dead or broken:

1. **Docker plumbing** — `just docker-build` depends on `build`, which now emits `autobahntestsuite-25.10.1-py3-none-any.whl`, but the recipe copies a `-py2-none-any.whl` and the Dockerfile is `FROM pypy:2-7-bullseye`. It cannot build.
2. **The flake's py2 half** — `nixpkgs-python` (CPython 2.7.18), `openssl_1_1` (insecure, explicitly permitted), `pkg-config`/`libffi`, and the `virtualenv<20.22` venv recipe existed solely to run the py2 suite locally. No py2 code remains.
3. **Backward dep pins** — `cbor2<6`, `cryptography<49` are transitive-via-autobahn (we import neither) and exist only because x86_64-macOS lacks their latest wheels. autobahn itself accepts `cbor2>=5.2.0` and `cryptography>=3.4.6`.

The suite's consumers are WebSocket implementers in any language who conformance-test from their own (often non-Python) CI. The user has confirmed that in this fork's case, only they run the suite, and they will use `nix run` / `uvx` — so Docker can leave master entirely.

## Goals / Non-Goals

**Goals:**
- Minimal tooling on `uv` (packaging/lock/run/publish) + `nix` (dev env), decoupled, with `just` retained as a slim command menu wrapping them.
- Latest dependencies, no backward pins.
- `uvx autobahntestsuite` / `pip` (PyPI) and `uv run wstest` (local) as the distribution/run channels.
- A flake shed of the py2 toolchain and the insecure-OpenSSL permission, in the user's preferred authoring style.

**Non-Goals:**
- Rebuilding or republishing any Docker image (the frozen `:25.10.1` is immutable and stays).
- Re-running the py3 migration's differential validation (that is `migrate-python3`'s remaining follow-up).
- Changing test-case behavior or the `wstest` CLI.
- Dropping Sphinx/RTD docs (kept, just de-`just`-ed).

## Decisions

### Decision 1: Remove Docker from master; preserve the frozen image out-of-tree

Delete `docker/` and the docker recipes. Before deleting, tag the current pre-change commit `v25.10.1-py2` so the last py2 source + Dockerfile remain retrievable. The published `crossbario/autobahn-testsuite:25.10.1` image is immutable on Docker Hub and is untouched.

*Alternative considered — Nix-built py3 image (`dockerTools.buildLayeredImage`):* attractive and would come free from the flake closure, but the user confirmed no external `docker run` consumers for this fork. Building/pushing an image nobody pulls is scope for its own sake. If a consumer ever appears, a `dockerTools` image is a small additive follow-up (the flake app already defines the closure it would wrap).

### Decision 2: Keep `nix` and `uv` decoupled — no `nix run` app, no uv2nix

Distribution is `uvx autobahntestsuite` / `pip install` (PyPI) and `uv run wstest` (local). Nix's role is *only* the reproducible dev shell; it puts `uv` on PATH and stops there.

We do **not** build a `nix run <repo>#wstest` app. Doing so would require teaching Nix to build the Python package from `uv.lock` — via **uv2nix** (extra input + overlay + build-backend edge cases) or **`buildPythonApplication`** (version drift from the lockfile). Both are a coupling layer whose sole payoff is one command, `nix run`, for a user who has Nix but not Python/uv.

That payoff is ~zero for this fork: the user is the only consumer and already has `uv` (it is in this very flake); anyone else with Nix gets `uv` from `nix develop` in one step, and anyone with Python gets the same zero-install via `uvx`. Adding a nix↔python bridge to a repo whose goal is *minimal* is anti-minimal.

```
  nix   → toolchain + dev shell (python3, uv, just, rust, nixd, alejandra)
  uv    → the Python package (uv.lock, uv build, uv run, uv publish)
  PyPI  → end-user distribution (uvx / pip)
          one seam: nix puts `uv` on PATH.
```

*Alternative considered — expose `apps.<sys>.wstest` via uv2nix:* rejected as above. If a Nix-only, uv-less consumer ever materializes, adding it later is an additive change; nothing here precludes it.

### Decision 3: Environment-marker pins (latest everywhere except x86_64-macOS)

Remove the blanket `cbor2<6` / `cryptography<49` constraints and replace them with **marker-scoped** constraints: `cbor2<6` and `cryptography<49` apply only on `platform_machine == 'x86_64' and sys_platform == 'darwin'`. uv's universal resolver forks on the marker — x86_64-macOS locks to the last wheel-available versions (cbor2 5.9.0, cryptography 48.0.1), every other platform (Linux, CI, Apple Silicon) locks to latest. No source builds, no Rust, on any platform.

*Implementation finding (supersedes the original "drop + Rust" plan):* dropping the pins outright makes uv's universal resolver pick cryptography 50.0.0 (highest with a valid sdist), which then fails to build on x86_64-macOS — cryptography's Rust build needs crates.io network access inside uv's build isolation plus OpenSSL, which is impractical on this machine. Rather than carry a Rust/OpenSSL build toolchain for one sunset platform, the marker keeps x86_64-macOS on wheels and keeps the dev shell minimal (no `rustc`/`cargo`/`pkg-config`). The marker is self-removing: on Apple Silicon it simply doesn't apply, so that platform already gets latest.

### Decision 4: Keep `just` as a thin menu over `uv`/`nix`; slim the recipes

`just` stays — it is the discoverable command menu (`just --list`) and one-word entry points, which `uv`/`nix` alone don't provide. But the justfile is cut to only the surviving tasks, each a thin wrapper:

```
  just dev       → nix develop         just build    → uv build
  just run …     → uv run wstest …     just publish  → uv publish
  just check     → nix flake check + uv run ty check
  just docs      → uv run sphinx-build (docs group)
```

Removed recipes: `install-python2*`, `create-venv`, `install*`, `docker-build`, `docker-test`, `publish-to-dockerhub`, and the py2 `test-*` variants. CI keeps calling `uv`/`nix` directly (already true for the `py3` job); the justfile is for humans.

*Alternative considered — remove `just` entirely:* the user briefly weighed this but chose to keep it. With py2/docker recipes gone the justfile is small, and `just --list` remains a nicer menu than `nix flake show` + README prose. Kept.

### Decision 5: Flake authoring style + shed the py2 toolchain

Adopt the user's patterns:
```nix
systems = nixpkgs.lib.systems.flakeExposed;
packages = nixpkgs.lib.genAttrs systems (system: let pkgs = import nixpkgs { inherit system; }; in { ... });
devShells.<sys>.default = pkgs.mkShell {
  packages = builtins.attrValues {
    inherit (pkgs) uv nixd alejandra rustc cargo pkg-config;
    python = pkgs.python3.withPackages (p: builtins.attrValues { inherit (p) uv; });
  };
};
```
Remove the `nixpkgs-python` input, `python2`, `openssl_1_1`, and the `permittedInsecurePackages`/CFLAGS/LDFLAGS wiring — all py2-only. Expose `apps.<sys>.wstest` and `packages.<sys>.default` (the app) alongside `devShells`.

**nixpkgs pin tension:** the flake currently pins `nixpkgs-26.05-darwin` (last release with x86_64-darwin). `flakeExposed` lists all standard systems; on 26.05 that is fine. When the dev machine moves to Apple Silicon, switch the input back to `nixpkgs-unstable` and `flakeExposed` is unconstrained. Recorded as a follow-up trigger, not done here.

### Decision 6: Differential reference — run the published image, or commit fixtures

The `migrate-python3` differential harness compares py3 output against the frozen py2 reference. With Docker gone from master, two ways to still get reference reports:
- **`docker run` the published `:25.10.1`** once to capture reference `index.json` — needs Docker installed at validation time only (not a build, not a distribution concern).
- **Commit the reference reports as static fixtures** under `test/differential/reference/` — makes validation fully Docker-free and version-controlled.

**Lean: commit fixtures.** It removes the last Docker dependency anywhere in the workflow and makes the reference diff reproducible in CI without a container runtime. Capturing them is a one-time `docker run` of the immutable image.

## Risks / Trade-offs

- [Dropping pins breaks the current Intel Mac if Rust is absent] → dev shell provides `rustc`/`cargo`; documented; moot on Apple Silicon.
- [Deleting `docker/` and `setup.py` is BREAKING for anyone scripting them] → the `v25.10.1-py2` tag and the published image preserve every prior artifact; README documents the new entry points.
- [No `nix run` for a Nix-only, uv-less consumer] → `nix develop` hands them `uv` in one step; `uvx` covers Python-havers; not a real audience for this fork. Additive to bring back later if needed.

## Open Questions

- Should the README keep a "testing a non-Python implementation" recipe using the *published* image (`docker run crossbario/autobahn-testsuite:25.10.1 …`)? It is the one place Docker is still the best tool for an external consumer, even though master no longer builds it. (Proposed: yes, a short note — it costs nothing and serves that audience.)
