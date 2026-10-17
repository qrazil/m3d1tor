# sourced by tests/test.sh: the file finder.
#
#   t_frecency, t_fuzzy, t_picker   unit checks (decay and state files, path ranking, the picker, hints)
#   finder_pty.py                   the pty property: over a tree of hostile names and files (wide, combining,
#                                   tabs, control bytes, ESC sequences, CRLF, binary, huge lines) the screen
#                                   the diff renderer produced equals a from-scratch redraw after every key,
#                                   the box keeps its frame, resizes included; ranking, the score column,
#                                   frecency and the clean run; skips cleanly when pyte is missing
#   bench/finder_bench.m31          the scorer on 100,000 paths; here only that it runs and that narrowing from
#                                   the previous matches finds what a full rescore finds
if [ ! -x "$WORK/m3" ]; then
    build m3 m3.m31
fi
if [ -x "$WORK/m3" ]; then
    if out=$(python3 tests/finder_pty.py "$WORK/m3" 2>&1); then
        note "finder_pty: $(printf '%s\n' "$out" | tail -1)"
    else
        bad "finder_pty" "$(printf '%s\n' "$out" | tail -25)"
    fi
fi
if build finder_bench bench/finder_bench.m31; then
    out=$("$WORK/finder_bench" 2>&1)
    if printf '%s\n' "$out" | grep -q MISMATCH || ! printf '%s\n' "$out" | grep -q 'typing'; then
        bad "finder_bench" "$(printf '%s\n' "$out" | tail -12)"
    else
        note "finder_bench: $(printf '%s\n' "$out" | grep 'full rescore  pom' | sed 's/^ *//')"
    fi
fi
