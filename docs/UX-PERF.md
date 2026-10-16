# UX and frame quality

How m3 is measured for feel, what it is held to, and what the numbers were before and after the
0.8.0 smoothness work. Harness: `bench/uxperf.py` (a real `m3` in a pty; Python 3 only; macOS-safe,
idle CPU and wakeups reported where `/proc` exists). Property test: `tests/anim_pty.py`.

    python3 bench/uxperf.py --m3d ./m3 [--rows 60 --cols 200] [--runs 30] [--only key,hold,resize,storm,idle,wrap]
                            [--env M3_NO_ANIM=1] [--no-sync-reply] [--json OUT] [--check]

A frame is one burst of output (or the bytes between `CSI ? 2026 h` and `l` when the editor uses
synchronized output; the harness answers its DECRQM question like a terminal that supports the mode,
`--no-sync-reply` like one that does not, which is how the "before" column was measured). The held-key test
simulates 30 Hz auto-repeat.

## Budgets

| what | budget | status |
|---|---|---|
| key to first byte, single-cell actions (`l`, `w`, a typed character, `j`), local pty | p50 under 5 ms, p99 under 8 ms on a quiet machine | p50 1.6-1.9 ms at 80x24, 4 ms at 200x60 on this box; p99 is dominated by other load here (see the caveat) |
| bytes written for a single-cell change | under 150 (the sync markers are 16 of them) | 42-46 for a cursor move, ~125 for a typed character |
| no full-screen repaint for a one-cell change, none for a scroll of a few lines | no row rewritten that did not change | held `j` writes 141 bytes a frame at 200x60 (was 2069) |
| held key at 30 Hz auto-repeat | one frame per key, every frame under 16 ms | 30.5 frames/s, key to frame p50 under 5 ms |
| animation | settles in under about 150 ms for any distance; input handled before the next frame | `<C-d>`: 7 frames, 100-115 ms; `G` over 3000 lines: 5-9 frames, 135-145 ms |
| idle | no animation timer; 4 ticks a second | see "Idle" |
| gross-regression guard in `tests/test.sh` (`--check`) | key to frame p99 under 100 ms, a cell move under 400 bytes, held key at least 10 frames/s, idle under 30 wakeups/s, 1 MB storms survive | enforced; everything else is reported, not failed |

## Results

Linux x86-64, 12 cores shared with other jobs (so tails are noisy; p50 and bytes are the stable columns),
`m3` v0.4.1 ("before") against 0.8.0 ("after", animation on unless noted), 3000-line source file, 30 runs per
row, sync-capable terminal for "after".

### 200x60

| action | before: first frame p50 (ms) / bytes | after: first frame p50 (ms) / bytes first, all frames | after: frames, settled (ms) |
|---|---|---|---|
| `j` | 4.1 / 62 | 4.2 / 78 | 1, 4 |
| `l` | 9.7 / 27 (noisy run; 2-4 typical) | 4.2 / 43 | 1, 4 |
| type a char | 4.0 / 107 | 4.3 / 126 | 1, 4 |
| `<C-d>` | 5.9 / 4101 | 4.4 / 84, 2447 | 7, 99 |
| `<C-f>` | 5.7 / 4146 | 4.3 / 85, 4487 | 8, 114 |
| `gg` | 5.0 / 4047 | 10.0 / 4081, 9551 | 5, 134 |
| `G` | 5.8 / 4173 | 11.8 / 4207, 10077 | 5, 135 |
| `/needle_rare<CR>` | 5.5 / 478 | 10.8 / 494, 494 (the jump was in the incsearch preview) | 1 |
| `n` | 5.6 / 86 | 11.8 / 102 | 1 |
| open picker (`<Space>ff`) | 13.1 / 5627, 9646 | 24.8 / 7600, 28975 | 3, 137 (fade) |
| `:vsplit` | 11.9 / 4915 | 15.2 / 4931 | 1 |
| `:split` | 6.8 / 2463 | 8.3 / 2467 | 1 |
| which-key | 8.1 / 41, 1518 | 5.5 / 57, 6575 | 5, 505 (fade) |

The +16 bytes are the synchronized-output markers; the rest of the "after" first-frame latencies above
single-cell actions were measured while the machine was loaded by other builds (the same binary measured 1.6-2.0
ms at 80x24 on a quiet moment, below).

### 80x24 (quiet moment)

| action | before p50 (ms) / bytes | after p50 (ms) / bytes first, all | frames |
|---|---|---|---|
| `j` | 1.7 / 61 | 1.9 / 77 | 1 |
| `l` | 1.5 / 26 | 1.8 / 42 | 1 |
| type a char | 1.6 / 105 | 1.8 / 124 | 1 |
| `<C-d>` | 2.1 / 1539 | 1.9 / 83, 1050 | 5 (82 ms) |
| `<C-f>` | 2.3 / 1557 | 2.1 / 84, 1741 | 6 (94 ms) |
| `G` | 2.6 / 1635 | 2.9 / 1619, 4432 | 6 (99 ms) |

### Held key, 30 Hz repeat

| | before: frames/s, bytes/frame, key to frame p50 (ms) | after: same | after, `M3_NO_ANIM=1` |
|---|---|---|---|
| hold `j` (200x60) | 30.5, 2069, 8.4 | 30.5, **141**, 4.3 | 30.4, 141 |
| hold `<C-d>` (200x60) | 30.8, 4058, 9.4 | 86, 978, 4.5 (a glide between keys) | 29.9, 4143 |
| hold `j` (80x24) | 30.5, 1245, 2.2 | 30.5, **176**, 1.7 | |
| hold `<C-d>` (80x24) | 30.5, 1528, 1.9 | 85.6, 386, 1.7 | |

Holding `j` at the bottom of a window scrolls by one line per key; that used to rewrite the window (about 2 KB a
frame at 200x60) and now writes a scroll region and the one new row.

### Full-screen redraw (a resize), one-cell change for comparison

| | before | after |
|---|---|---|
| resize, bytes / frames | 4750 / 1 | 4766 / 1 (inside one synchronized frame) |
| one cell | 27 bytes | 43 bytes (16 of them the markers) |

### Input storms

| input | before | after |
|---|---|---|
| paste of 1 MB (bracketed) | 0.35 s to quiet, 1 frame, 4451 bytes | 0.25 s, 1 frame, 4477 bytes |
| 1 MB of `jk` keys (unbracketed) | 29.7 s, 33 frames | 31.3 s, 23 frames (still alive, still correct) |

The key storm is bound by the engine and the per-event work, not by output (2 KB written in all); it is
unchanged by this work and not a regression.

### Wrapped file (1000 lines of ~340 columns, `:set wrap`)

| action | before p50 (ms) / bytes | after p50 (ms) / bytes first, all |
|---|---|---|
| `j` | 8.9 / 58 | 11.1 / 74 |
| `<C-d>` | 12.9 / 10777 | 12.5 / 81, 5480 (4 frames, 100 ms) |
| `G` | 13.1 / 10844 | 13.2 / 10847, 29382 (5 frames) |

Wrapped lines scroll with their screen rows, so a scrolled view is still matched row for row.

### Idle

Both versions: about 4.5 % CPU and 900-940 context switches a second on an idle editor. This is not the
application's timer: with the 250 ms idle tick the main thread still wakes several hundred times a second and the
runtime's 14 worker threads about 190 times a second each. It comes from the m31 runtime (`rt.c` / the scheduler's
timers), so it is reported rather than worked around; the editor's own
animation timer is not running while idle (the loop asks for 250 ms ticks, `Loop.animate_ms`, after 1.5 s without
input and nothing pending).

## What the property test checks (`tests/anim_pty.py`)

For 19 sequences (half pages, pages, `G` / `gg`, distant lines, search and `n`, `zt zz zb`, `H M L`, `scrolloff`
at the ends, wheel notches and bursts, `<C-e>` / `<C-y>`, Visual then scroll, yank-scroll-put, wrap, macros, dot,
which-key, picker) the same keys are typed into an animating editor and one with `M3_NO_ANIM=1`; after every
step both screens are identical (text, cursor cell, reverse flags). Every intermediate frame (cut at the
synchronized-output markers) keeps the status line equal to the final one and stays on the path between the
start and the goal. Also: `j` / `k` are one frame; `<C-d>` is several and under 300 ms; idle writes no byte;
`--no-anim`, `$M3_NO_ANIM`, `TERM=dumb`, `:set noanimate` are one frame; without truecolor scrolling still glides and
no 24-bit blend is written; the yank flash appears and clears; Insert asks for a bar cursor and quitting puts
the shape and the terminal modes back; the scrollbar draws and a click in it jumps; a resize leaves consecutive lines
and a status line.
