#!/usr/bin/env bash
# Build medit (`medit.m31`) into a real executable.
#
#   M31_ROOT=/path/to/m31 bash scripts/build.sh            -> ./medit
#   M31_ROOT=/path/to/m31 bash scripts/build.sh -o name    -> ./name
#
# `medit.m31` imports github.com/qrazil/tui as `import tui.TUI_app;`. The
# `deps` file names the exact commit; the first compile fetches it into
# `.m31-deps/` and records it in `deps.lock`.
#
# Needs LANGC (the m31c compiler binary, v0.3.2 or later) and M31_ROOT (a
# checkout of github.com/qrazil/m31, or an extracted release's runtime SDK
# containing config.sh and runtime/). There is no pre-built runtime library.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -z "${M31_ROOT:-}" ]; then
    echo "M31_ROOT is not set -- point it at a checkout of github.com/qrazil/m31" \
         "(or an extracted release's runtime SDK). See this script's header." >&2
    exit 1
fi
if [ ! -f "$M31_ROOT/config.sh" ] || [ ! -d "$M31_ROOT/runtime" ]; then
    echo "M31_ROOT=$M31_ROOT does not look like an m31 checkout" \
         "(expected $M31_ROOT/config.sh and $M31_ROOT/runtime/)" >&2
    exit 1
fi
. "$M31_ROOT/config.sh"
. "$M31_ROOT/runtime/arch.sh"

out=medit
[ "${1:-}" = "-o" ] && out=${2:?-o needs a name}

LANGC=${LANGC:-./m31c}
CC=${CC:-cc}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

if [ ! -x "$LANGC" ]; then
    echo "compiler not found or not executable: $LANGC" >&2
    exit 1
fi

"$LANGC" --emit-c medit.m31 -o "$tmp/medit.c"
"$CC" -O2 -pthread -I "$M31_ROOT/runtime" -o "$out" "$tmp/medit.c" \
    "$M31_ROOT/runtime/rt.c" "$M31_ROOT/runtime/scheduler.c" \
    "$M31_ROOT/$RT_REACTOR_C" "$M31_ROOT/$RT_CTX_ASM"
echo "$out"
