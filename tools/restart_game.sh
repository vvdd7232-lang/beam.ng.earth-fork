#!/bin/sh
# Restart the game directly. Set BNGE_GAME_DIR to its installation directory.
set -eu
: "${BNGE_GAME_DIR:?Set BNGE_GAME_DIR to the BeamNG.drive install folder}"
exe="$BNGE_GAME_DIR/BinLinux/BeamNG.drive.x64"
[ -x "$exe" ] || { echo "Game executable not found: $exe" >&2; exit 1; }
pkill -x BeamNG.drive.x64 || true
cd "$BNGE_GAME_DIR/BinLinux"
exec "$exe" "$@"
