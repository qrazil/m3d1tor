# sourced by tests/test.sh: motion and rendering quality.
#
#   t_anim            unit checks of the scroll scheduler, pacer and colour blends
#   anim_pty.py       the pty property: an animation never changes the final screen,
#                     intermediate frames are consistent, kill switches work
#   bench/uxperf.py   latency / bytes / frame-rate harness, run with --check (fails only
#                     on gross regressions; real numbers are in docs/UX-PERF.md)
unit t_anim
if [ ! -x "$WORK/m3" ]; then
    build m3 m3.m31
fi
if [ -x "$WORK/m3" ]; then
    if out=$(python3 tests/anim_pty.py "$WORK/m3" 2>&1); then
        note "anim_pty: $(printf '%s\n' "$out" | tail -1)"
    else
        bad "anim_pty" "$(printf '%s\n' "$out" | tail -25)"
    fi
    if out=$(python3 bench/uxperf.py --m3d "$WORK/m3" --runs 8 --hold-seconds 1 --idle-seconds 2 --only key,hold,storm,idle --check 2>&1); then
        note "uxperf: no gross regression"
    else
        bad "uxperf" "$(printf '%s\n' "$out" | tail -15)"
    fi
fi
