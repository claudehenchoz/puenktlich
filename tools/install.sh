#!/usr/bin/env bash
# Install pinned external tools into .tools/bin (needs Go >= 1.22 and git).
#   gorender      voxel -> OpenTTD sprite renderer   (github.com/mattkimber/gorender, MIT)
#   cargopositor  voxel cargo/variant compositor     (github.com/mattkimber/cargopositor, MIT)
# Bump a pin: change the SHA below, run this script, run `make test`, commit.
set -euo pipefail

GORENDER_REPO=https://github.com/mattkimber/gorender
GORENDER_SHA=75c5e3cfc58405c9e6c1be5f2b9f13dea4751a2f
CARGOPOSITOR_REPO=https://github.com/mattkimber/cargopositor
CARGOPOSITOR_SHA=6d0bee1a082bb0395e84b70a112e5b3216d69ec0

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/.tools/src"
BIN="$ROOT/.tools/bin"
mkdir -p "$SRC" "$BIN"

command -v go >/dev/null || { echo "error: Go toolchain not found (https://go.dev/dl/)" >&2; exit 1; }

fetch() {  # name repo sha
  local dir="$SRC/$1"
  if [ ! -d "$dir/.git" ]; then
    git clone --quiet "$2" "$dir"
  fi
  git -C "$dir" fetch --quiet origin "$3" 2>/dev/null || git -C "$dir" fetch --quiet --unshallow origin || true
  git -C "$dir" checkout --quiet "$3"
}

build() {  # name output
  echo "building $1 @ $(git -C "$SRC/$1" rev-parse --short HEAD)"
  (cd "$SRC/$1" && go build -o "$BIN/$2$(go env GOEXE)" ./cmd)
}

fetch gorender "$GORENDER_REPO" "$GORENDER_SHA"
build gorender gorender
fetch cargopositor "$CARGOPOSITOR_REPO" "$CARGOPOSITOR_SHA"
build cargopositor cargopositor

echo "done: $(ls "$BIN" | tr '\n' ' ')"
