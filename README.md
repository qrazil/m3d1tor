# m3d1tor

A terminal text editor with Vim key bindings, written in
[m31](https://github.com/qrazil/m31) on the [tui](https://github.com/qrazil/tui)
library. IDE-lite: keyboard first, no toolbar or menu chrome, discoverable
through which-key, a command palette and a keymap help picker. (`medit` is the
design codename that `DESIGN.md` still uses.)

**Status: v0.1.0 (default plugins).** The Vim engine is checked against `nvim --headless` on
more than 38,500 generated and hand-written cases (20 known divergences, listed in
`tests/oracles/known_divergences.txt`); on top of it sit the built-in plugins that make it a daily editor:
a fuzzy finder with async sources (rg / fd / git when installed, a built-in walker and grep when not), which-key for
every prefix, a keymap table that mirrors the owner's Neovim leader keys, git signs with hunk stage / reset /
preview / blame, a statusline and bufferline, harpoon-style pinned files, quickfix, a terminal pane, `:!` `:r !` and
`!{motion}` filters, label jump, line move, indent guides, TODO highlighting, last-position restore and a minimal
language server client. Every built-in can be switched off (`:PluginDisable NAME`, `:Plugins`). See
[docs/KEYMAP.md](docs/KEYMAP.md) for every default key (generated from the same table the editor uses) and DESIGN
section 12 and 13 for the plugin framework and the LSP client.

Options that change behaviour are checked against nvim one by one: `scrolloff`, `sidescroll`,
`sidescrolloff`, `wrap`/`nowrap` scrolling, `whichwrap`, `iskeyword`, `textwidth`
with `formatoptions` (auto-wrap, `gq`, comment leaders), `tabstop`, `shiftwidth`,
`softtabstop`, `expandtab`, `smarttab`, `autoindent`, `ignorecase`, `smartcase`,
`wrapscan`, `startofline`, `smartindent`, `list`/`listchars`, `cursorline`,
`cursorcolumn`, `colorcolumn`. Known limits: no command-line window, no fold methods besides manual,
a reduced `=` indent (`cindent` is not implemented; `smartindent` is), `formatoptions` `a` and `n`, `linebreak`, many
options are stored but do not change behaviour yet, no tree-sitter, no undo files, and the terminal pane is
line oriented (no full-screen programs). `m3d1tor --version` prints the version.

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
- Syntax highlighting for c, cpp, go, javascript/typescript, json, m31, markdown,
  python, rust, sh, toml and yaml (`:syntax on|off`, `:set syntax=NAME`); the
  colours are the terminal's palette, light or dark by `COLORFGBG` or `:set background=`.
- Command-line completion: `<Tab>` / `<C-n>` and `<S-Tab>` / `<C-p>` complete ex
  commands, option names (long and short), file and directory names and buffers.
- Manual folds: `zf` `zF` `:fold`, `zo zO zc zC za zA zv zR zM zd zD zE zj zk`.
- File tree sidebar (neo-tree style): `<Space>e` toggles it, `<Space>E` reveals the
  current file, `:Neotree [toggle|show|focus|close|reveal|refresh|DIR]`. Rows are
  folders first, git status letters (M A D R ? !) sit at the right and folders
  carry the worst status of what is inside; the tree follows the buffer.
  `:Explore` and `:e DIR` still open the netrw-style listing in a window.
- Which-key popup for the leader sequences.
- Comment toggle `gc` / `gcc` / visual `gc`, with the comment string chosen by file type
  (`:set commentstring=`), matching Neovim 0.11's built-in `gc`.
- A keymap file in Vim syntax: `:map` / `:noremap` for n, x, o, i, c modes, `:unmap`,
  `:mapclear`, `let mapleader`, `:source` (see below).

The editing engine is tested differentially against `nvim --headless` (31k+ cases): motions, operators, text objects,
counts, dot repeat, registers, undo, visual modes, macros, marks, search, ex commands, insert-mode keys (including
`<C-r>` forms, `<C-n>`/`<C-p>` completion, `<C-t>`/`<C-d>`, `gR`), `:set` options, soft wrap and screen-line motions.

Display: soft wrap (`:set nowrap` for horizontal scrolling), `gj gk g0 g^ g$ gm`, `:set number relativenumber list`,
`hlsearch` highlighting (`:noh`).

More

- Surround as in vim-surround: `ys{motion}{char}`, `yss`, `yS`, `ySS`, `ds{char}`, `cs{old}{new}`, `cS`, and `S` / `gS` in
  Visual mode (`)`/`b`, `(`, `]`/`r`, `}`/`B`, `>`/`a`, quotes, `t` and `<` for tags with attributes kept by `cs`, `f` and `F` for
  function calls, `l` for LaTeX, `p`, `s`, a space prefix). The engine is checked against the plugin itself.
- Auto pairs as in auto-pairs: `(` `[` `{` `'` `"` `` ` `` and the triples, a closing key steps over, `<BS>` in an empty pair deletes
  both, `<Space>` pads, `<CR>` between brackets opens a line. `:set noautopairs` turns it off.
- Git gutter: `+` added, `~` changed, `_` removed lines against HEAD in a sign column, `]c` / `[c` to jump between changes
  (`:set nogitsigns` turns it off). Lower-case marks show as letters in the same column; `:marks`, `:registers`, `:jumps`,
  `:changes` list as Vim does and `<Space>fm` is a marks picker.
- System clipboard: `"+` and `"*` use pbcopy / pbpaste (macOS), wl-clipboard, xclip or xsel; `:set clipboard=unnamedplus` makes
  every yank and put use it.
- Windows: `:resize`, `:vertical resize`, `<C-w>` `+ - < > _ | =` `H J K L` `r R x`; closing a modified buffer's last window is E37.
- Display: soft wrap, `incsearch`, `hlsearch`, `number`, `relativenumber`, `list`; `gj gk g0 g^ g$ gm`.
- Directory listings (`:Explore`): `R` rename, `D` delete, `%` new file, `d` new directory, `gh` toggle dotfiles.

## Keys

Normal-mode `<Space>` is the leader; a pending sequence shows which-key after a short delay.

| keys | action |
|---|---|
| `jk` | Insert mode: back to Normal |
| `<Space>ff` / `<Space><Space>` | find files |
| `<Space>fr` `fd` `fq` | recent files, lines of the buffer, quickfix |
| `<Space>fb` / `<Space>,` | buffers |
| `<Space>fg` / `<Space>/` | live grep |
| `<Space>fc` / `<Space>:` | command palette |
| `<Space>?` / `<Space>fh` | keymap help |
| `<Space>e` / `<Space>fe` | file explorer (`-` goes up) |
| `<Space>bn` `bp` `ba` `bd` `bl` | next, previous, alternate, delete, list buffers |
| `<Space>sv` `sh` `se` `sc` `z` `o` | split right, split below, equalise, close, close, only this window |
| `<Space>n` | new buffer |
| `<Space>w` / `<Space>qq` / `<Space>qa` | write, quit, quit all |
| `<C-w>` `s v n c q o w W p t h j k l` | window commands |
| `<C-^>` | alternate buffer |
| `:w` `:q` `:q!` `:wq` `ZZ` | write and quit |

In a picker, `<C-s>` / `<C-v>` open the hit in a split below / beside.

## Built-in plugins

| plugin | default keys | what it does |
|---|---|---|
| finder | `<Space>ff fg fr fb fd fq fh fc fk fo fm fx fs ft fw` | files, live grep, recent, buffers, lines of the buffer, quickfix, keys, commands, options, marks, diagnostics, symbols, TODOs, word under cursor; `<C-t>` marks, `<C-q>` sends to quickfix |
| whichkey | after 400 ms of any pending prefix | `<Space>`, `g`, `z`, `[`, `]`, `<C-w>`, `"`, `'`, operators |
| explorer | `<Space>e` | file tree sidebar (see below) |
| git | `<Space>gg gf gb gc gC gs gr gp gB gt`, `]c [c ]h [h` | changed files, branch checkout, remote branches, commit log with preview, hunk stage / reset / preview, blame line, signs |
| surround | `ys ds cs`, Visual `S`, `<Space>sa sd sr` | vim-surround |
| comment | `gc` `gcc` | language-aware toggle |
| autopairs | insert mode | bracket and quote pairing |
| statusline | | mode, file, git branch and hunk counts, E/W counts, filetype, position; bufferline with two or more buffers |
| bracketed | `[b ]b [q ]q [d ]d [h ]h [t ]t` | buffers, quickfix, diagnostics, hunks, TODO comments |
| harpoon | `<Space>ha he hn hp hd`, `<Space>1`..`9` | pinned files per project (`~/.local/state/m3d1tor`) |
| move | `<A-j> <A-k> <A-h> <A-l>` | move or shift the line or the Visual selection |
| jump | `<Space>j` | type a character, then a label |
| guides | | indent guides (`:set noindentguides`) |
| todo | `<Space>ft`, `]t` | highlight and list TODO FIXME HACK XXX NOTE WARN PERF BUG |
| terminal | `<Space>t`, `:terminal [cmd]` | a shell on a pty; `<C-\><C-n>` leaves to Normal mode, `i` goes back |
| session | | last cursor position of each file, recent files |
| lsp | `K gd grr grn gra`, `<Space>cr ca cf ll xx`, `:Lsp ...` | diagnostics, hover, definition, references, rename, code action, format |

`:Plugins` lists them, `:PluginDisable NAME` / `:PluginEnable NAME` switch one (put the lines in the keymap file).
`:Keys` or `<Space>?` browses every key. `:set nojk_escape` turns the Insert-mode `jk` off.

Shell: `:!cmd` shows the output, `:{range}!cmd` filters lines, `:r !cmd` and `:r file` read, `!{motion}` and
Visual `!` start the filter command line; `%` is the file name and `!` the previous command. They match nvim
(corpus 103) for commands that do not need a terminal; use `:terminal` for interactive programs.

LSP: servers are found on `$PATH` by file type (rust-analyzer, gopls, pyright-langserver or pylsp, clangd,
typescript-language-server, lua-language-server, marksman, bash-language-server) and started on demand;
`:Lsp server LANGUAGE COMMAND...` sets one, `:Lsp info|start|stop|hover|definition|references|rename NAME|format|action`.

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

## macOS (Apple silicon) in three lines

    curl -fsSL https://github.com/qrazil/m31/releases/download/v0.4.3/m31-macos-arm64.tar.gz | tar -xz -C /tmp && export M31_ROOT=/tmp LANGC=/tmp/m31c   # the m31 compiler and runtime
    git clone https://github.com/qrazil/m3d1tor && cd m3d1tor && bash scripts/build.sh      # needs Xcode command line tools (cc); first run fetches tui
    ./m3d1tor FILE   # Terminal.app (256 colours) and iTerm2 / kitty / WezTerm (truecolor) work; --no-mouse turns mouse reports off

Colour depth follows `COLORTERM` / `TERM`; `--no-mouse` (or `M3D1TOR_NO_MOUSE=1`) leaves the mouse to the terminal.

## Build

    export M31_ROOT=/path/to/m31          # a checkout or an extracted release (config.sh + runtime/)
    export LANGC=$M31_ROOT/target/release/m31c
    bash scripts/build.sh                 # -> ./m3d1tor   (bash scripts/build.sh -o NAME to rename)
    ./m3d1tor FILE...

Needs m31 v0.4.3 or later (the `proc` module); the first compile fetches the pinned `tui` into
`.m31-deps/` (the commit is in `deps`, recorded in `deps.lock`).

## Test

    M31_ROOT=... LANGC=... bash tests/test.sh

`tests/test.sh` is the single entry point: `m31c fmt --check -r .`, `m31c lint .`,
the unit programs (`tests/test_units.sh`), the nvim oracles
(`tests/test_engine.sh`, skipped with a note when `nvim` is missing) and pty end-to-end
runs of the real binary (`tests/e2e.py`, which needs `pyte`: `pip install pyte`; skipped with a note
otherwise). The oracles need `nvim` 0.11 and `python3`. `bash scripts/oracle.sh --fuzz --seed 7 --cases 500`
runs the engine oracle on its own.

## File tree keys

With the tree focused (`<C-w>h` from the leftmost window, `<Space>e`, a click):

| keys | action |
|---|---|
| `j k gg G <C-d> <C-u> <C-f> <C-b>` | move |
| `l` `<CR>` `o` | open the file / expand the folder |
| `h` | collapse the folder, or go to the parent |
| `s` `v` `t` | open in a split / vertical split / vertical split (there are no tab pages) |
| `a` | add: `:Neotree add DIR/` is typed for you, a trailing `/` makes a folder |
| `d` | delete: `:Neotree delete PATH` is shown, Enter confirms, Esc cancels |
| `r` `m` `c` | rename / move / copy to: the command line holds the old path |
| `y` `x` `p` | copy, cut, paste into the folder under the cursor |
| `H` | toggle hidden files |
| `/` | filter (fuzzy; Esc clears it) |
| `z` | collapse all |
| `R` | refresh git status |
| `P` `i` | preview / info |
| `.` `u` `<BS>` | make the folder the root / go up a folder |
| `?` | help |
| `q` | close the tree |
| `<C-w>l` `<C-w>w` `<Esc>` | back to the editor window |
| `:` `<Space>` | the command line and leader keys work as everywhere |

Options: `:set treeglyphs` (Nerd Font icons), `:set treewidth=40`, `:set treehidden`.

## Layout

    m3d1tor.m31        entry point: arguments, terminal check, tui loop
    engine/            editing core, no terminal dependency
                       buffer text charclass case key parse num nrfmt motion textobj
                       register regex search editor ex vim view
    ui/                drawing, input and navigation
                       app keymap plugin window picker picker_view fuzzy files grep ignore tree git clip
                       sources state vt lsp shell
    tests/             test.sh (entry), t_*.m31 unit programs, MED_check.m31, oracles/
    scripts/           build.sh, oracle.sh, gen_keymap.sh (docs/KEYMAP.md from the keymap table)
    docs/              KEYMAP.md (generated)
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
tarballs to the GitHub Release. The release is marked a pre-release; v0.0.2 is tagged on the
user's instruction. Version 0.1.0 is not tagged by the branch that introduced the default plugins; the lead tags after review.
