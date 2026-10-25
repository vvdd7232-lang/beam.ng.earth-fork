#!/bin/sh
# Build the grass-keeping preload library (README.md): tools/gcpatch/build/libbngearth_gcpatch.so
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$HERE/build"
${CC:-gcc} -shared -fPIC -O2 -Wall -Wextra -pthread -o "$HERE/build/libbngearth_gcpatch.so" "$HERE/bngearth_gcpatch.c"
echo "built $HERE/build/libbngearth_gcpatch.so"
echo 'Run python launcher.py --game-dir /path/to/BeamNG.drive to preload the library.'
