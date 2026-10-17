# The file finder: ranking, relevance, frecency and drawing

`<Space>ff` (and `:Files`, the recent-files picker) lists files and filters them as you type. This page is the
design of what it puts first and why, how a row is drawn, and what is stored. Code: `ui/MED_fuzzy.m31` (the
scorer), `ui/MED_frecency.m31` (frequency and recency), `ui/MED_picker.m31` (the list and the pool),
`ui/MED_picker_view.m31` (drawing). Tests: `tests/t_fuzzy.m31`, `t_frecency.m31`, `t_picker.m31`,
`tests/finder_pty.py`. Numbers: `bench/finder_bench.m31`.

## 1. What comes first: name before path, then a tidy match

A query is space separated terms that all have to match (`'` exact, `^` prefix, `$` suffix, `!` not, as in fzf).
For a plain (fuzzy) term the scorer first asks what the term is **to the file name** (the part after the last
`/`), and only then how tidy the placement is. The answer is a *tier*:

| Tier | The query is ... | Example for `pom` |
|---|---|---|
| 7 | the file name | `pom` |
| 6 | the file name without its extension | `pom.xml`, `parent/pom.xml` |
| 5 | the start of the file name | `pomelo.txt` |
| 4 | a run inside the file name (best boundary wins) | `xpomx.txt`, `my_pom.txt` |
| 3 | a tight subsequence of the file name (spanning at most twice the query), an initialism (`fb` for `foo_bar`), or a run that crosses a `/` (`ui/med` in `ui/MED_app.m31`) | `poxm.txt` |
| 2 | a compact subsequence of the whole path (spanning at most four times the query) | `src/po/m.txt` |
| 1 | anything else that is a subsequence: scattered | `pxxxxxxoxxxxxxxx_fbdjdk_m` |

The score is `tier * 100000 + refinement`, so nothing a lower tier can earn lifts a candidate over the tier
above (a long streak of matches, a frecency boost). The refinement:

* tiers 5 and 4: how much of the name the query covers (`100 * length(query) / length(name)`), plus 10 times the
  boundary bonus for a run: the shorter name is the closer match, a run after `_`, `-`, `.` or `/` beats one in
  the middle of a word;
* tiers 3 to 1: the fzf-style placement score. The placement is the one fzf finds first (the earliest end, pulled
  back to the latest start), scored as `MED_fuzzy`'s dynamic program scores a placement: `+16` per matched
  character, `+4` (or the boundary bonus, if larger) when a match directly follows the one before, `+8` at the
  start and after `/`, `+7` after `_ - . space` and at a lower-to-upper step (the first character counts double),
  `-3` to open a gap and `-1` per further skipped character.

Ties, in order: the higher score, the shorter path, the earlier in the source's order. The order of equal
candidates is therefore the same on every run (a test checks it). Smart-case holds throughout: a capital in the
query makes the term case sensitive.

The dynamic program (`Query.positions`) is still what picks the characters to highlight, because it finds the
best placement and the highlight is where the eye goes; the ranking does not run it.

The test cases from the report: for `pom`, `pom.xml` and `parent/pom.xml` (tier 6, the shorter path first) come
before `poxm.txt` (tier 3), which comes before `pxxxxxxoxxxxxxxx_fbdjdk_m` (tier 1).

## 2. Relevance percentage

Each row of the files and recent pickers shows `NN%` at its right edge when there is a query. It is derived
from the tier and from how tidy the match is inside it, so it reads as "how good a match", 0 to 100:

| Tier | Percent |
|---|---|
| 7 | 100 |
| 6 | 97 |
| 5 | 88 to 94, by how much of the name the query is |
| 4 | 72 to 87 (3 more on a boundary) |
| 3 | 50 to 71, by the placement score as a share of a perfect placement |
| 2 | 28 to 49 |
| 1 | 5 to 27 |

With several terms the percentage is the average of the terms'. A frecency boost adds up to 5 points (never past
100) and puts a dim `*` before the percentage. With an empty prompt only the `*` shows. `:set nofinderscore`
hides the whole column (and gives the list its width back).

## 3. Frecency

`MED_frecency` keeps, per file, a heat that goes up by one for each visit and halves every `finderhalflife`
days (default 14):

    heat_now  = heat_then * 2 ^ (-(now - then) / half_life)  [+ 1 on a visit]
    boost     = 150 * heat / (heat + 1)                      (integer, 0 to 149)

So ten visits last week outweigh one today, and a file left alone for a few months is as cold as one never opened.
One fresh visit is a boost of 75; the boost is added to the score, and 150 is a thousandth of a tier, so frecency
reorders matches **of the same kind** and never lifts a worse kind over a better one. The `*` shows from a boost
of 45 (a visit within about the last two weeks, or several older ones).

* **With a query:** ranked by `score + boost`.
* **With an empty prompt:** the visited files first, hottest then most recent; then every other file in the order
  the source (`fd`, `rg --files` or the built-in walk) lists it.
* **What counts as a visit:** a file becoming the current buffer (counted once per switch, on the state tick,
  and once more when the editor closes, so a quick open and quit still counts), not a cursor move.

Files and where they live:

| File | Content |
|---|---|
| `$XDG_STATE_HOME/m3/frecency`, else `~/.local/state/m3/frecency` | one line per file: `HEAT_MILLI TAB EPOCH_SECONDS TAB ABSOLUTE_PATH` (the heat in thousandths, as of that second) |

Bounds and safety: at most 2000 lines (the hottest) are written, a file whose heat fell under 0.02 is forgotten,
the order of lines is fixed for a given state, and the file is written to `frecency.tmp` and renamed over the
real one, so a reader (another editor) never sees half a file. A clean run (`--keymap NONE`) has no state
directory at all: it reads and writes nothing, and the finder is ordered by the source alone. Failures to read
or write the state are silent: it is a convenience, never a reason to fail.

## 4. Cost

`bench/finder_bench.m31` ranks 100,000 paths (an `i7-8750H`, one core, m31 v0.6.0, `-O2`). "Real" is the
first 100,000 files `find` lists under `/usr`, `~/.cargo`, `~/.nvm` (60 characters on average); "synthetic" is
generated words with 1 to 5 directories.

| Query | synthetic | real |
|---|---|---|
| empty | 12 ms | 9 ms |
| `pom` | 33 ms | 39 ms |
| `po` | 37 ms | 47 ms |
| `e` (96,000 matches) | 46 ms | 50 ms |
| `mdapp` | 23 ms | 33 ms |
| `src app rs` (three terms) | 28 ms | 86 ms |
| `zzzq` (no match: the scan itself) | 20 ms | 29 ms |

Typing `controller`, per keystroke: without narrowing 42 42 38 36 31 30 30 30 31 30 ms (synthetic), 49 59 57 55 47 42
34 33 31 31 ms (real); with narrowing 41 37 29 24 15 12 11 10 11 10 ms (synthetic) and 49 56 53 46 32 20 9 2 1 0 ms
(real). The scorer the finder had before ranked `pom` in 117 ms (synthetic) and 147 ms (real), with the dynamic
program on every candidate; a first version of the tiered scorer that ran it only on the candidates that needed
it still took 130 to 560 ms per keystroke on the real paths, so the placement is now the allocation-free one
above, and the dynamic program is left to highlighting.

What makes it fast:

1. **No allocation for ASCII paths.** The byte-level matcher (`single_tier`, `fast_tier`, `window`) reads the path
   with `byte_at`, decides tiers 7 to 4 by scanning, and finds the placement of the lower tiers by the two-pass
   window; only a non-ASCII path or term takes the code point version (`window_cp`), which gives the same answer
   (a test runs both on the same paths and compares).
2. **Narrowing.** When the new prompt extends the last one (and neither holds `!` or `$`), only the files the last
   prompt matched are looked at: every match of `pomx` is a match of `pom`. The pool is dropped when the entries
   change.
3. **One ranking per batch of keys.** The picker marks itself stale on a key that edits the prompt and the front
   end ranks once per batch of input (`Picker.refresh`), so a paste or a held key costs one ranking, not one per
   character.
4. **Sorting integers.** A match is one integer (score, shorter, earlier, percent packed in 62 bits), so ordering
   100,000 of them is a plain integer sort (7 ms), and only the top 5000 are turned into rows.

Opening the finder costs one pass over the entries for frecency: 28 ms for 100,000 files against a state file of
2000 (a string concatenation and a map lookup each). The first keystroke is the expensive one, because every
file is a candidate; about 45 to 50 ms at 100,000 files is the floor set by reading 6 MB of path bytes through
`byte_at`. A repository of 10,000 files costs a tenth of that.

## 5. Drawing, and why the finder used to leave a mess

Two defects made the box and the preview corrupt themselves; both are fixed in the `tui` library
(commit `0b132ce`, version 0.9.1), not worked around here.

* **Control characters were written to the terminal.** A cell holding a tab, a carriage return or ESC was sent as
  it was. A tab moved the cursor to the next tab stop, a CR (every line of a CRLF file) returned it to column 0, an
  ESC started a sequence, so a preview of a file with colour codes could clear the screen or shift the rest of the
  row, and the right border with it. `Buffer.set_str`, `set` and `fill` now put the control's picture in its cell
  (U+2400 plus the code, U+2421 for DEL, U+FFFD for a C1 control). The preview also drops a trailing CR and
  expands tabs to the next multiple of four columns once, when the file is read.
* **Terminals disagree about the width of an emoji ZWJ sequence, a flag or a variation-selector emoji.** The buffer
  holds one two-column cell for the cluster; a terminal that adds up code points draws four or six, and every
  cell after it in the row lands in another column. The renderer now puts the cursor back with an absolute move
  after such a cluster, never walks across one to save bytes, and writes the two columns after it again whenever
  it is written or goes away (`TUI_diff.is_uncertain`), which repairs the cells a wider drawing overdrew. On a
  terminal that agrees it costs a few bytes.
* The finder drew a name one code point at a time, which drops every combining mark and joiner and splits a flag
  into two cells; it now draws one grapheme cluster at a time.

`tests/finder_pty.py` is the property that keeps this true: it opens the finder over a tree of hostile names and
files (long, wide, combining, tabs, control bytes, ESC, CRLF, Latin-1, binary, one 200,000 character line), and
after every key, every query, every resize and CTRL-N / CTRL-P it compares the screen the diff renderer made with
a from-scratch redraw of the same state (a resize away and back is always a full frame) and checks the frame of
the box. Before the fixes it failed 31 of 73 quick checks; it passes all 173.

**Repainting.** CTRL-L in a picker writes every cell again (`Loop.should_repaint`), and so does a focus-in
report, for the case where something else wrote on the terminal while it was away. The preview reads the file
again when the selection changes, when the file's size or modification time changed, and its scroll position
follows the focus line on every frame; nothing is cached across a resize (the pane is redrawn from state every
frame), only the file read is (an expensive thing, kept until its inputs change).

**Key hints** are one dim row set into the bottom border of the box (`╰─ Enter open  ^S split  ... ─╯`), chosen
by the picker (files: open, split, vsplit, mark, quickfix, hidden, ignore, redraw, close; the palette: run; the
explorer adds `- up`), most useful first and cut at the right when the box is narrow. A side picker (themes)
has none.

## 6. Knobs

| Knob | Where | Default |
|---|---|---|
| `:set finderscore` / `nofinderscore` | option | on |
| `:set finderhalflife=N` | option, days | 14 |
| `TIGHT_SPAN`, `COMPACT_SPAN` | `ui/MED_fuzzy.m31` | 2, 4 |
| `TIER_STEP`, the tier numbers | `ui/MED_fuzzy.m31` | 100000, 1 to 7 |
| `MATCH_SCORE` and the bonuses | `ui/MED_fuzzy.m31` | 16, 4, 8, 7, 7, 8, 3, 1 |
| `BOOST_CAP`, `MARK_FROM`, `MAX_ENTRIES` | `ui/MED_frecency.m31` | 150, 45, 2000 |
| `BOOST_PERCENT` | `ui/MED_fuzzy.m31` | 5 |
| `MAX_SHOWN` | `ui/MED_picker.m31` | 5000 rows ranked and kept |

## 7. Not done

* The ranking looks at each term on its own; "src app" (a directory and a name) is two terms, each placed by
  its own tier, not one path pattern.
* No per-project frecency: one heat per absolute path, shared by every project that contains it (which is what
  one wants for a file that lives in two checkouts' worth of use, and wrong for two checkouts of one repo).
* Grep, symbols and the command palette keep the generic scorer (`Query.score`): they have no file name, so
  the tiers would mean nothing, and no relevance column.
