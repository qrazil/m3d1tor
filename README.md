# m3d1tor

A terminal text editor with Vim key bindings, written in
[m31](https://github.com/qrazil/m31) on the [tui](https://github.com/qrazil/tui)
library. IDE-lite: keyboard first, no toolbar or menu chrome, discoverable
through which-key, a command palette and a keymap help picker. (`medit` is the
design codename that `DESIGN.md` still uses.)

**Status: 0.0.x, pre-release.** The v0.1.0 acceptance bar (DESIGN section 9:
"at least as capable as Helix, with Vim bindings") is not met yet: the git
gutter, surround, comment toggle, auto pairs, marks UI and the
recorded benchmarks are still to do. No release has been tagged and none will be
until it is. The `version` in `deps` is not bumped by the reorganisation.

## Features

- Modal editing with Vim grammar: motions, operators, text objects, counts,
  registers, macros, dot repeat, marks, visual modes (char, line, block), `<C-a>` / `<C-x>`.
- Undo tree (`u`, `<C-r>`, `g-`, `g+`, `:earlier`, `:later`).
- Search (`/ ? n N * #`), `:s`, `:g`, `:v`, `:normal`, `:sort` and the rest of the
  ex subset in DESIGN section 2. A purpose-built Vim-regex engine (no
  backreferences or lookaround).
- Buffers and windows: `:e :ls :b :bn :bp :bd`, `:split :vsplit :close :only`,
  `<C-w>` commands, mouse click, drag and wheel.
- Pickers: files, buffers, live grep, commands, keymap help, explorer; `.gitignore` aware.
- Which-key popup for the leader sequences.
- A keymap file in Vim syntax: `:map` / `:noremap` for n, x, o, i, c modes, `:unmap`,
  `:mapclear`, `let mapleader`, `:source` (see below).

The editing engine is tested differentially against `nvim --headless` (15k+ cases).

## Keys

Normal-mode `<Space>` is the leader; a pending sequence shows which-key after a short delay.

| keys | action |
|---|---|
| `jk` | Insert mode: back to Normal |
| `<Space>ff` / `<Space><Space>` | find files |
| `<Space>fb` / `<Space>,` | buffers |
| `<Space>fg` / `<Space>/` | live grep |
| `<Space>fc` / `<Space>:` | command palette |
| `<Space>?` / `<Space>fh` | keymap help |
| `<Space>e` / `<Space>fe` | file explorer (`-` goes up) |
| `<Space>bn` `bp` `ba` `bd` `bl` | next, previous, alternate, delete, list buffers |
| `<Space>sv` `sh` `se` `sc` `o` | split right, split below, equalise, close, only this window |
| `<Space>w` / `<Space>qq` / `<Space>qa` | write, quit, quit all |
| `<C-w>` `s v n c q o w W p t h j k l` | window commands |
| `<C-^>` | alternate buffer |
| `:w` `:q` `:q!` `:wq` `ZZ` | write and quit |

In a picker, `<C-s>` / `<C-v>` open the hit in a split below / beside.

## Keymap file

`~/.config/m3d1tor/keymap.vim` (or `$XDG_CONFIG_HOME/m3d1tor/keymap.vim`, or the file
named by `$M3D1TOR_KEYMAP`, or `m3d1tor -u FILE`; `-u NONE` reads none) is a list of ex lines:

    let mapleader = " "
    nnoremap <leader>w :w<CR>
    inoremap jj <Esc>
    xnoremap < <gv

`"` starts a comment line. A map on `<Space>` replaces the built-in leader menu, and a
map starting with `j` in Insert mode replaces the built-in `jk`. Behaviour follows nvim
(checked in the oracle corpus); `<buffer>` and `<expr>` maps are refused (E474), and maps do
not apply inside macros, `.` or `:normal`.

## Build

    export M31_ROOT=/path/to/m31          # a checkout or an extracted release (config.sh + runtime/)
    export LANGC=$M31_ROOT/target/release/m31c
    bash scripts/build.sh                 # -> ./m3d1tor   (bash scripts/build.sh -o NAME to rename)
    ./m3d1tor FILE...

Needs m31 v0.4.0 or later; the first compile fetches the pinned `tui` into
`.m31-deps/` (the commit is in `deps`, recorded in `deps.lock`).

## Test

    M31_ROOT=... LANGC=... bash tests/test.sh

`tests/test.sh` is the single entry point: `m31c fmt --check -r .`, `m31c lint .`,
the unit programs (`tests/test_units.sh`) and the nvim oracles
(`tests/test_engine.sh`, skipped with a note when `nvim` is missing). The oracles
need `nvim` 0.11 and `python3`. `bash scripts/oracle.sh --fuzz --seed 7 --cases 500`
runs the engine oracle on its own.

## Layout

    m3d1tor.m31        entry point: arguments, terminal check, tui loop
    engine/            editing core, no terminal dependency
                       buffer text charclass case key parse num nrfmt motion textobj
                       register regex search editor ex vim view
    ui/                drawing, input and navigation
                       app keymap window picker picker_view fuzzy files grep ignore
    tests/             test.sh (entry), t_*.m31 unit programs, MED_check.m31, oracles/
    scripts/           build.sh, oracle.sh
    DESIGN.md          plan, plugin audit, architecture, oracle plan, v0.1.0 acceptance
    RENAMES.md         old-to-new import and file table for the grouped layout

Every module is `MED_<name>`, imported by path (`import engine.MED_buffer;`) and
used by its last segment (`MED_buffer.Buffer`). `engine/` imports nothing from
`ui/` and `tui`; `ui/` imports `engine/` and `tui`.

## Release

CI (`.github/workflows/test.yml`) runs `tests/test.sh` on Linux x86-64, Linux
aarch64 and macOS arm64 for every push to master. Pushing a `v*` tag runs
`.github/workflows/release.yml`: the test workflow is a hard precondition, then
it builds `m3d1tor` on the same three platforms and attaches
`m3d1tor-linux-x86_64`, `m3d1tor-linux-aarch64` and `m3d1tor-macos-arm64`
tarballs to the GitHub Release. Tagging is a human step and waits for v0.1.0
acceptance (Status above).
