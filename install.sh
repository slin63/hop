#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Install the Python CLI (provides the `_hop` command on PATH).
if command -v uv >/dev/null 2>&1; then
  uv tool install --force "$REPO_DIR"
elif command -v pipx >/dev/null 2>&1; then
  pipx install --force "$REPO_DIR"
else
  echo "hop: need 'uv' or 'pipx' to install. Get one:" >&2
  echo "  uv:   https://docs.astral.sh/uv/getting-started/installation/" >&2
  echo "  pipx: https://pipx.pypa.io/stable/installation/" >&2
  exit 1
fi

# 2. Install the shell wrapper to a stable location (clone can be deleted after).
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/hop"
mkdir -p "$DATA_DIR"
cp "$REPO_DIR/shell/hop.sh" "$DATA_DIR/hop.sh"

# 3. Wire the wrapper into the user's shell rc.
case "$(basename "${SHELL:-}")" in
  zsh)  RC="$HOME/.zshrc" ;;
  bash) RC="$HOME/.bashrc" ;;
  *)    RC="" ;;
esac

LINE="source \"$DATA_DIR/hop.sh\""
if [ -n "$RC" ]; then
  if ! grep -qsF "$LINE" "$RC"; then
    printf '\n# hop directory jumper\n%s\n' "$LINE" >> "$RC"
    echo "hop: added wrapper to $RC"
  else
    echo "hop: wrapper already in $RC"
  fi
  echo "hop: run 'source $RC' or restart your shell, then try: hop add"
else
  echo "hop: add this line to your shell rc, then restart your shell:" >&2
  echo "  $LINE" >&2
fi
