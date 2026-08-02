# Copyright (c) typedef int GmbH, Germany, 2025. All rights reserved.
#
# Minimal command menu wrapping uv (Python packaging) and nix (dev env).
# Everything here is a thin alias; uv and nix remain the source of truth.

set positional-arguments := true

PACKAGE_VERSION := "25.10.1"

# Default recipe - show available commands
default:
    @echo ""
    @echo "  Autobahn|Testsuite - WebSocket Protocol Conformance Testsuite"
    @echo "  version {{PACKAGE_VERSION}} | https://autobahntestsuite.readthedocs.io"
    @echo ""
    @just --list
    @echo ""

# Enter the reproducible dev shell (or use direnv: `direnv allow`)
dev:
    nix develop

# Run wstest (e.g. `just run -m fuzzingserver`)
run *args:
    uv run wstest {{args}}

# Install/sync the project environment from uv.lock
sync:
    uv sync --group dev

# Build wheel + sdist
build:
    uv build

# Publish to PyPI (requires credentials / UV_PUBLISH_TOKEN)
publish: build
    uv publish

# Checks: flake evaluation + advisory type check + fuzzing smoke test
check:
    nix flake check
    uv run ty check || true
    uv run python test/differential/smoke_py3.py

# Build the documentation (Sphinx, via the `docs` extra)
docs:
    uv run --extra docs sphinx-build -b html docs docs/_build/html
