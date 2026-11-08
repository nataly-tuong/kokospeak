#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
UV_LOCAL="$ROOT/.runtime/uv"
mkdir -p "$UV_LOCAL"
if [[ -x "$UV_LOCAL/uv" ]]; then
  UV_BIN="$UV_LOCAL/uv"
elif command -v uv >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
else
  echo "Installing KokoSpeak's private Python installer..."
  BOOTSTRAP="$(mktemp)"
  trap 'rm -f "$BOOTSTRAP"' EXIT
  if command -v curl >/dev/null 2>&1; then
    curl --fail --location --retry 5 --connect-timeout 30 https://astral.sh/uv/install.sh --output "$BOOTSTRAP"
  elif command -v wget >/dev/null 2>&1; then
    wget --tries=5 --timeout=120 https://astral.sh/uv/install.sh -O "$BOOTSTRAP"
  else
    echo "curl or wget is required for the initial download." >&2
    exit 1
  fi
  UV_UNMANAGED_INSTALL="$UV_LOCAL" sh "$BOOTSTRAP"
  UV_BIN="$UV_LOCAL/uv"
fi
export UV_HTTP_TIMEOUT=120
export UV_HTTP_RETRIES=5
# Explicit Python selection avoids the active Conda or virtualenv version.
unset VIRTUAL_ENV
"$UV_BIN" run --no-project --no-config --python 3.12 "$ROOT/scripts/setup.py" --uv "$UV_BIN" "$@"
