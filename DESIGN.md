# medit design

`medit` (working codename, trivially renamable) is a terminal text editor with
Vim key bindings, written entirely in m31 on top of the `tui` library. It is an
IDE-lite: no toolbar, no menu chrome, keyboard first, discoverable through a
which-key popup, a command palette and `?`.

Goal for v0.1.0: at least as capable as Helix, with Vim bindings. Section 9
defines that concretely and says honestly which parts are impossible in m31
today.

Rules that shape everything below:

* Everything is written in m31. If m31 cannot do something, we stop and record
  a gap (section 11); we do not add Rust or work around it with a shell.
* nvim 0.11 is the oracle for the editing engine (section 7). Behaviour is
  whatever `nvim --headless -u NONE` does, defaults included.
* Naming follows the m31 naming decision. The project prefix is `MED_`.

## 1. What the user actually runs (plugin audit)

Read from `~/.vimrc` (vim-plug era), `~/.config/nvim/init.lua`,
`lua/config/keymaps.lua`, `lua/plugins/*.lua` and `lazy-lock.json`.

Core settings the editor must make default or one-line configurable: leader is
Space, 4-space expandtab, `number` + `relativenumber`, `ignorecase` +
`smartcase`, `scrolloff=8`, `nowrap`, `undofile`, `mouse=a`, `hlsearch` +
`incsearch`, `cursorline`, `signcolumn=yes`, `splitright`/`splitbelow`,
`clipboard=unnamedplus`. Keymaps in use: `jk` as Escape in insert mode,
`<leader>w` write, `<leader>z` close, `<leader>n` new file, `<leader>o` only,
`<leader>R` reload all buffers, `<leader>sv/sh/se/sc` split/balance/close,
`<leader>b` buffer manager, `<leader>e` explorer, `<leader>?` which-key,
`<leader>ha/he/hp/hn/1..n` harpoon, `<leader>h*` git hunks, `<leader>xx...`
trouble, `<leader>a` aerial, `<leader>ll`/`]]`/`[[` diagnostics.

### Decision table

Legend: **v0.1** = built in and required for the v0.1.0 tag. **later** = wanted,
after v0.1.0, with the reason it waits. **never** = out of scope, with the
reason. "Milestone" is the build phase that delivers it (M1 engine, M2 tui,
M3 picker; M4 is the stretch work between M3 and the tag).

| Plugin(s) | What the user does with it | Decision | Reasoning |
|---|---|---|---|
| fzf-lua, fzf.vim, mini.pick, mini.extra | files, live grep, buffers, git files, oldfiles, quickfix, git branches/commits | **v0.1** (M3): files, buffers, grep, oldfiles, command palette, jumplist. Branch/commit pickers later | This is the feature Helix is most loved for and the one the user reaches for most. The picker is one widget, reused by every list. Git pickers need the git library: later |
| mini.files, neo-tree, NERDTree | `<leader>e` explorer | **v0.1** (M4): directory picker with `-` to go up and a plain read-only directory buffer (`:Explore`). Editable (oil-style rename/delete by editing) later | Helix ships exactly a picker-based explorer. A persistent sidebar tree needs splits plus a tree view and buys little over the picker; the directory buffer gets all Vim motions for free |
| which-key (vim-which-key) | `<leader>?`, leader popup | **v0.1** (M3) | Core promise (no chrome, still discoverable). The tui crate already ships `TUI_menu.WhichKey` |
| nvim-autopairs, auto-pairs | insert-mode pairing | **v0.1** (M4), default on, one option to disable | Insert-mode only, small, and Helix has it on by default |
| comment (vim-commentary), Comment.nvim | `gc`, `gcc` | **v0.1** (M4): `gc{motion}`, `gcc`, visual `gc`; comment string chosen by file extension | Oracle-testable: nvim 0.11 has native `gc` |
| mini.surround, vim-surround | `<leader>sa/sd/sr/sf/sh`; `ys/ds/cs` | **v0.1** (M4): vim-surround keys `ys{motion}{char}`, `ds{char}`, `cs{old}{new}`, visual `S`; the user's `<leader>s*` aliases are keymap data on top | Helix has `ms/md/mr`; this is the Vim-shaped equivalent. Pure text transform on the engine, no new machinery |
| built-in marks + marks.nvim | named marks | **v0.1**: marks `a-z A-Z ' \` [ ] < >` are engine features (M1). Sign-column marks later | Marks are part of Vim grammar, oracle-testable |
| harpoon2 | pinned file list, `<leader>1..n` | **later** | Needs a persisted per-project list and a small menu; the buffer picker, `'A` global marks and the jumplist cover the need until then |
| buffer_manager | `<leader>b` | **v0.1** (M3): it is the buffer picker | Folded into the picker |
| splits (`<leader>s*`, `<C-w>`) | vsplit/split/balance/close/only | **v0.1** (M4): window tree with `:split`, `:vsplit`, `<C-w>hjkl`, close, only, equalise | The user's keymaps show splits are used daily, and Helix has them. The engine models `Window` (cursor, scroll, jumplist) separately from `Buffer` from day one so splits are a UI feature, not a redesign. Phases 0-3 render a single window |
| gitsigns, vim-gitgutter | gutter signs, hunk nav, stage/reset hunk, blame, `ih` | **v0.1** gutter signs and `]c`/`[c` (M4), via the stdlib `diff` module against the HEAD blob read through the gitui git modules. Stage/reset hunk, blame, `ih`: later | Helix has a diff gutter, so the tag needs one. It depends on gitui's `GIT_*` modules as a dependency |
| fugitive, neogit, diffview, git-conflict | full git UI | **never** in medit | The user has gitui. `<leader>g` suspends medit and runs gitui through `os.run` (inherits the terminal): later |
| LSP: vim-lsp, nvim-lspconfig, mason, asyncomplete, blink.cmp, nvim-cmp, nvim-java, trouble, aerial | diagnostics, completion, goto, hover, rename, symbols | **later, blocked**: needs a child process with piped stdin/stdout. `os.run` only inherits stdio. Gap G1 | Not workable by shelling out through temp files without being a hack; per the rules this is a stop-and-report item |
| conform (rustfmt, ruff, stylua, prettier) | format on save | **later, blocked** by G1 for filters; running `rustfmt <file>` in place and reloading is possible with `os.run` alone but is deferred until G1 is decided | Same family as filters (`!`, `:r !`) |
| nvim-dap | debugger | **never** (v0.x) | Needs LSP-class process plumbing plus a UI; far outside IDE-lite |
| treesitter, vim-polyglot, markview, nvim-highlight-colors, colorizer | highlight, indent | **later**: a hand-written lexical highlighter (per-language token rules, no parse tree) for Rust, Python, C, Lua, m31, Markdown, JSON, shell. Tree-sitter itself is impossible (G3) | Gives colours without a parser runtime. Not v0.1.0-blocking, but listed in the Helix gap in section 9 |
| nvim-ufo, folds | `zR`, `zM`, folds | **later**: indent-based folds only | Needs fold state in the view layer; not core to editing correctness |
| todo-comments | highlight TODO | **later** (a highlighter rule) | Cosmetic |
| mini.move | move line/selection | **v0.1** (M4): `<M-j>`/`<M-k>` line move, visual too | Tiny, uses ordinary edits |
| mini.bracketed | `]b [b ]c ...` | **v0.1** for `]b [b` (buffers), `]c [c` (hunks), `]d [d` once diagnostics exist | Keymap data |
| editorconfig | indent/charset per file | **later** (v0.1.x) | Easy, but not needed to be capable |
| vim-repeat | `.` for plugins | **v0.1**, built in: every command goes through the dot-repeat recorder | The grammar design makes plugins a non-issue |
| incsearch / hlsearch | search UX | **v0.1** (M2/M3) | Built in |
| lualine, vim-airline | statusline | **v0.1** (M2): built-in statusline with mode, file, modified flag, position | Plain widget |
| themes (tokyonight, nightfox, gruvbox-material) | colours | **v0.1**: one built-in theme (dark, 16-colour fallback) + one light; theme as data. The user's three: later | Theme is a `Map` of style names to `TUI_style.Style` |
| mini.indentscope, indent-blankline, indentLine | indent guides | **later** | Cosmetic |
| neoscroll | smooth scroll | **never** | Animation through a polling loop is the wrong trade |
| nvim-notify | popup notifications | **v0.1**: messages go to the command-line area; a `:messages` history | No popups |
| LuaSnip, ultisnips | snippets | **later** (static templates with tab stops) | Without LSP the snippet source is a file we would also ship |
| floaterm, `:terminal` | embedded shell | **never** (G4: no pty) | Cannot be built without a pty |
| vim-startify | start screen | **later**; `<leader>fo` oldfiles picker covers it | |
| markdown-preview | browser preview | **never** | Needs a browser and a server; out of IDE-lite |
| nvim-devicons | glyphs | **never** by default (font dependent); optional later | |
| no-neck-pain | centred layout | **never** | |
| Copilot, CopilotChat, codecompanion, avante, minuet, claude-code | AI | **never** inside the editor | Needs network + process plumbing and is not an editor concern. Claude Code runs in the neighbouring terminal pane |
| neotest | test runner | **never** (disabled in the user's config) | |

Everything marked **v0.1** has an owner phase. The ones that are not in the
three phases of this build (M1-M3) are the M4 list: splits, explorer,
surround, comment, autopairs, mini.move, git gutter. They are designed for now
(window model, command registry, keymap data) so they do not require rework.

## 2. Architecture

Flat layout like gitui: library modules at the repo root, `MED_` prefix on
library file names, a lowercase entry file `medit.m31`.

### 2.1 Layers

```
 term / tui          (from the tui dependency, not ours)
   |
 MED_view, MED_status, MED_picker_ui, MED_help     UI: draw state into TUI buffers
   |
 MED_editor                                        session: buffers, windows, mode machine
   |
 MED_command + MED_keymap                          named commands; keymaps as data
   |
 MED_operator, MED_motion, MED_textobj, MED_search, MED_ex     the Vim engine
   |
 MED_buffer, MED_edit, MED_undo, MED_register, MED_text, MED_key  text model
```

The bottom three layers import no terminal code. The engine is driven by one
function, `Editor.feed(key)`, plus accessors. That is also the whole oracle
harness API.

### 2.2 Text model

* **Buffer**: a `List<str>` of lines, no line terminators stored, plus
  `final_newline`/`line_ending` flags for load and save. The narrow interface
  is `line_count()`, `line(row)`, `text(range)` and one mutator,
  `splice(range, replacement) -> Edit`. Nothing outside `MED_buffer` indexes the
  list. A rope can replace it behind that interface if benchmarks demand it.
  Why a line array: m31 `str` is immutable UTF-8, `List.insert` is a memmove
  (spike: 1000 insert/remove pairs at the middle of a 100,000-line list is
  immeasurable), every Vim operation is line-oriented, and a rope in m31 would be
  a tree of refcounted nodes we would have to write and tune first.
  Known cost: editing one very long line is O(line length) per keystroke;
  benchmarks (section 8) will quantify.
* **Positions** are `(row, col)` with `col` a byte offset into the line, always
  on a grapheme cluster boundary. nvim reports byte columns, so oracle
  comparison needs no translation. Display columns exist only in the view and in
  `curswant`.
* **Grapheme awareness**: `MED_text` wraps `unicode.graphemes`/`unicode.width`
  with an ASCII fast path (a line whose bytes are all `< 0x80` never calls
  unicode). `l`, `h`, `x`, `~`, `r` etc. move by cluster; nvim 0.11 does too.
* **Edit** = `(start, removed_text, inserted_text)`; **Transaction** = ordered
  `List<Edit>` plus cursor before and after. A transaction is the unit of undo.
  Applying a transaction runs its edits in order; inverting it reverses the list
  and swaps removed/inserted. Positions in each edit are relative to the buffer
  at the moment that edit is applied (sequential semantics), which is simpler
  than Helix's offset ChangeSet and enough with a line array.
* **Undo tree**: nodes `{seq, parent, children, transaction, time}`; `u`/`<C-r>`
  walk parent / latest child; `g-`/`g+` walk by `seq` through the tree;
  `:earlier`/`:later` by count first, time later. One undo block per normal-mode
  command, per insert session (from `i`/`a`/`o`/`c...` to Escape), per `:s`, per
  `:g`, per macro-level undo exactly as nvim blocks them. `undofile` persistence
  is a later serialisation of the tree.
* **Registers**: `"` unnamed, `0`, `1-9` (shifting on large/linewise deletes
  exactly as Vim), `-` small delete, `a-z` and `A-Z` (append), `_` black hole,
  `/` last search, `:` last command, `.` last inserted text, `%` file name. Each
  value is `{text lines, kind: Char | Line | Block(width)}`. `+`/`*` map to the
  system clipboard through OSC 52 (write only, see G5).
* **Marks**: per-buffer `a-z`, `'`, `` ` ``, `[`, `]`, `<`, `>`, `.`, `^`, `"`;
  global `A-Z`. Marks track edits (adjusted by transactions).
* **Window**: `{buffer, cursor, curswant, scroll_top, scroll_left, jumplist,
  changelist, visual anchor/kind}`. Buffer ≠ window so splits are free later.

### 2.3 Commands and keymaps as data

Every action is a named command: `move.word_forward`, `op.delete`,
`edit.join_lines`, `mode.insert`, `file.write`, `picker.files`, ... A command has
a **kind**: `Motion`, `Operator`, `TextObject`, `Action`, `Ex`, `Insert`,
`Visual`, `Picker`, `Window`. The registry is a `Map<str, CommandId>` onto an
`enum CommandId`; a single exhaustive `match` in `MED_command` dispatches
(m31 has no function values and `match` works only on enums, so an enum with one
dispatch function gives compile-time exhaustiveness and no per-command type
boilerplate).

Keymaps are **data**: `MED_defaults` is a list of
`(mode, key notation, command name, args, description)` rows, e.g.
`("n", "gg", "move.file_start", "", "go to first line")`,
`("n", "<leader>ff", "picker.files", "", "find files")`. At start they are
compiled into one trie per mode. `description` feeds which-key and `?`. A user
keymap file (`~/.config/medit/keymap`, same row syntax) can override rows; v0.1
ships the file reader because the `jk` escape and leader mappings are on the
user's critical path.

Modes: `Normal`, `OperatorPending`, `Visual` (kind Char/Line/Block), `Insert`,
`Replace`, `Cmdline` (`:` `/` `?`), `Picker`, `Help`. Insert mode keymaps resolve
the longest-match with a timeout (`jk`), using the 250 ms-class tick in the
tui loop (configurable `timeoutlen`).

### 2.4 Vim grammar onto commands

Input arrives as keys (`int`: code point, control codes as themselves, special
keys in a private range, modifier bits above bit 24). The normal-mode machine
keeps a **pending key list** and after each key asks the parser:

```
command := ["x] [count] ( action
                        | operator [count] motion_or_object
                        | operator operator          (dd, yy, >>, gUU, g??)
                        | motion )
```

`parse(pending) -> Complete(Parsed) | NeedMore | Invalid`. Reparsing the pending
list on every key is stateless, obviously correct and cheap (pending lists are
at most a handful of keys). Operator-pending lookups use the OperatorPending
trie (motions and text objects); counts multiply (`2d3w` is 6 words). Forced
motion types `dv` `dV` `d<C-v>` are parsed there.

* **Motions** return a `MotionResult {target position, kind: Charwise | Linewise,
  inclusive, jump?}`; as plain cursor moves they set the cursor and `curswant`.
* **Text objects** return a range (start, end, kind) given count and
  inner/around.
* **Operators** take `(range, kind, register)`, build one Transaction, set cursor
  and registers. The special cases (`cw` acts like `ce`, `dw` at end of line, the
  `d` linewise-promotion rule for multi-line exclusive motions) are implemented
  where Vim implements them and are what the oracle exists to check.
* **Count** is carried as `Option<int>`; `.` substitutes a new count for the
  original one as Vim does.
* **Dot repeat**: the editor records the full key list of the last *change*
  (prefix, register, operator, motion/object, and for insert-starting changes all
  typed keys through Escape). `.` replays that list with the count replaced. This
  is also why autopairs/surround/comment need nothing special: they are ordinary
  key sequences. Replay is guarded against recursion.
* **Macros**: `q{reg}` appends typed keys to a recording; stopping stores them in
  the register as text (special keys as private-range code points), `@{reg}`/`@@`
  feeds them through `feed` with the count, aborting the rest of a macro on the
  first failing motion or search as Vim does.
* **Visual modes**: anchor + cursor in the window; `v`, `V`, `<C-v>`, `o`, `O`,
  `gv`, `$` in block mode, then operator keys applied immediately to
  `'<,'>`-style ranges, `I`/`A`/`c` block insert replicating to every line.
* **Ex**: `:` parses a command line (`range`, `command`, `bang`, `args`) for
  `:s`, `:g`/`:v`, `:d`, `:y`, `:m`, `:t`, `:>`/`:<`, `:j`, `:normal`, `:w`, `:q`,
  `:wq`, `:x`, `:e`, `:b`, `:set`, `:noh`, `:sp`/`:vsp`, `:!` (inherit-terminal
  run only). Regex: Vim regex are translated (magic, `\v`, `\<`/`\>`, `\{n,m}`,
  `\zs` ...) onto the stdlib `regex` module (Pike VM, no backreferences or
  lookaround). Gaps against Vim regex are listed in the known divergences
  (section 7).

## 3. Rendering

`MED_view` is a `TUI_widget.Widget`. It draws the text window, line numbers
(absolute, relative, hybrid), signs column, cursorline, visual selection,
search highlights, statusline, and the command/message line into a
`TUI_buffer.Buffer`; `TUI_diff` does the minimal-update. Cells are graphemes
(wide characters take two). Tabs expand with `tabstop`. `nowrap` + horizontal
scroll is the default (the user's setting); soft wrap is later.

The loop is the tui `Loop` pattern (read with timeout, `Action.Redraw`), with the
gitui-style idle `Ticker` for timeouts (`jk`), message expiry and picker results
streaming in. Resize is detected by polling `term.size()` each tick (there is no
SIGWINCH, G2); the tick drops to 30 ms while the user is active so resize feels
immediate, and back to 250 ms when idle.

## 4. Picker

One `Picker` widget serves files, buffers, grep, oldfiles, jumplist, commands
(palette), help topics, explorer. It is: a prompt line, a list (`TUI_list_table`
`ListView`), a preview pane (file head or grep context), and a source that
produces items asynchronously.

* **Sources** run in a `spawn`ed green thread and push batches over a channel;
  the loop drains it each tick, so a 100k-file walk never blocks input.
* **Files**: `fs.walk` from the project root (nearest ancestor with `.git`, else
  cwd) honouring `.gitignore`, `.git/info/exclude` and a hidden-file toggle
  (`<C-h>`), `<C-i>` toggles ignore (the user's fzf-lua `ctrl-i`). The gitui
  `GIT_ignore` matcher is the reference for the rules.
* **Grep** ("ripgrep-like, in m31"): walk with the same ignore rules, skip files
  that contain NUL in their first 8 KiB, split into lines, match either with a
  literal search (`str.index_of` after smart-case folding, the fast path when the
  query has no regex metacharacters) or with `regex.compile` (fixed-string toggle
  `<C-f>`). Each file is searched in its own task; results stream as
  `path:line:col:text`. `<C-q>` sends all to a quickfix-style list. A literal
  scan over a few hundred MB is memory-bandwidth bound in this runtime; the
  benchmark plan includes it against `rg` honestly.
* **Fuzzy scoring** (the scorer is a pure module, `MED_fuzzy`): an fzf-v2
  style Smith-Waterman-like dynamic program, chosen because it is the algorithm
  users already have intuition for (fzf, fzf-lua, Helix's nucleo are all this
  family) and it is well specified:
  1. Smart-case (case-insensitive unless the query has an uppercase letter),
     ASCII fold fast path, Unicode fold for the rest.
  2. Subsequence prefilter: cheap `O(n)` reject (the vast majority of items).
  3. For survivors, a DP over `query × candidate` filling a best-score matrix
     with: match `+16`; consecutive matches `+4` (carry); boundary bonus `+8` after
     `/`, `+7` after `_ - . space`, `+7` camelCase lower→upper, `+8` first char
     of the string; first query char bonus ×2; gap open `-3`, gap extend `-1`.
     Backtrack for highlight positions only for the visible rows.
  4. Extended syntax: space-separated terms are ANDed; `^abc` prefix; `abc$`
     suffix; `'abc` exact substring; `!abc` negation.
  5. Ranking: score desc, then shorter candidate, then earlier match start, then
     original order (the stdlib `sort` is stable).
  Incremental: extending the query rescans only the previous survivors.
  Scoring runs in chunks (e.g. 4k items per tick) so typing stays responsive on
  large sets; the list always shows the best results found so far.
* **Palette**: `:` with an empty line or `<leader>:` opens the command picker
  over the registry (name + description + bound keys).
* `?` opens a searchable keymap help (same data), which-key shows the next-key
  popup after the leader (or any prefix) times out.

## 5. File explorer

Decision: **no persistent sidebar**. `<leader>e` opens a picker rooted at the
directory of the current file (directories first, `-` goes up, Enter opens or
descends, `<C-d>` shows hidden files). `:Explore` opens a directory as a normal
read-only buffer (netrw-lite) so `j/k//`, `gg` etc. work. Editable rename/delete
(oil / mini.files style) is a later feature built on the same buffer plus a
diff-the-listing-on-write step.

## 6. Module list (v0.1)

The tree is grouped (m3d1tor 0.0.x, see RENAMES.md): `engine/` is the editing core with no
terminal dependency, `ui/` is everything that draws, picks or lays out; `m3d1tor.m31` is the entry
at the root. Modules are imported by path (`import engine.MED_buffer;`); names keep the `MED_`
prefix. The rows below are the original plan, including modules not written yet.

```
engine/MED_key.m31  key codes, notation <Esc> <C-v> <leader> <CR> <Tab> ...
engine/MED_text.m31  cluster boundaries, widths, word/WORD/blank classes
engine/MED_buffer.m31  line array, splice, load/save, line endings
MED_edit.m31       Edit, Transaction, apply/invert
MED_undo.m31       undo tree
engine/MED_register.m31  register file
engine/MED_motion.m31  w b e ge W B E gE 0 ^ $ g_ | f F t T ; , % ( ) { } H M L gg G ...
engine/MED_textobj.m31  iw aw iW aW is as ip ap i( a( i[ i{ i< i" i' i` it at ...
MED_operator.m31   d c y > < = gu gU g~ g? gq J gJ ~ r ...
engine/MED_search.m31  / ? n N * # g* g#, Vim-regex translation
engine/MED_nrfmt.m31  <C-a> <C-x> g<C-a> g<C-x>: decimal/0x/0b numbers (64-bit signed; Vim's are unsigned 64-bit, so a decimal of 2^63 or more is left alone)
engine/MED_ex.m31  ex-command parser and executor: ranges (patterns, marks, offsets, `;`), `:s` (flags, `&&`, `~`, `\r`, `\u`/`\U`/`\e`, multi-line patterns), `:g`/`:v`, `:d :y :pu :m :t/:co :j :> :< :k :normal :undo :redo :earlier :later :sort :z :registers`, `:set` of the supported options, `|` chains, `@:` and cmdline history (Up/Down); an ex line is one undo block. `:earlier Nf` / `:later Nf` follow file writes (the editor records the undo node of every write in `saved_nodes`). A whole `@a` (with a count) is one undo block. Insert-mode `<C-o>` runs one Normal command and restarts the insert (cursor, `Insstart` and `<C-w>`/`<C-u>` limits follow nvim; `:normal` keeps the pending restart). `{Visual}@a` is `:'<,'>normal @a` for linewise Visual and runs inside Visual for `v`/`<C-v>`. Not supported: the command-line window (`q:`, `q/`), `.` repeating directly after an insert `<C-o>` (nvim replays the half-finished insert in an order we do not model), `<C-o>` combined with `.`/`g;`/`` `. `` marks (those need the changelist), the nvim K_SPECIAL artifact that a macro recorded with `r`/`f`/`t` + a char picks up when more commands follow, `:s///c`, `\=` replacement expressions, `:!`, `:r`, `:a`/`:i`/`:c`, time-based `:earlier 10s`, an operator followed by `:` (`d:cmd<CR>`), the `.`/`(`/`)` marks, jumplist/changelist. Corpus 52 keeps only the insert-`<C-o>` cases that match nvim; the rest (a column off by one after a `<C-o>` motion from an `A` insert at the end of a line, a block insert inside `<C-o>`, the ``` `` ``` mark, registers or `@a` inside `<C-o>`) are known gaps. `:sort` and `:z` match nvim for the cursor, not the printed text
ui/MED_keymap.m31  leader table (rows: keys, label, action), prefix/leaf lookup, which-key timeout
MED_command.m31    command registry and dispatch
engine/MED_editor.m31  modes, pending keys, dot, macros, jumplist
ui/MED_fuzzy.m31  scorer: smart-case, fzf-style DP, extended syntax (^ $ ' !), highlight positions; tests/t_fuzzy.m31
ui/MED_ignore.m31  .gitignore / .git/info/exclude matcher; tests/t_ignore.m31
ui/MED_files.m31  project root, file walk with ignore and hidden toggles, directory listing
ui/MED_grep.m31  corpus + search (literal fast path, regex, smart-case); tests/t_grep.m31
ui/MED_picker.m31  picker state machine (prompt, ranking, selection, keys); tests/t_picker.m31
ui/MED_picker_view.m31  picker drawing: list, highlights, preview pane
ui/MED_window.m31  window layout tree: split, remove, placement into screen rectangles, directional neighbours; tests/t_window.m31
engine/MED_view.m31  drawing
ui/MED_window.m31  window layout tree: split, remove, placement into screen rectangles, directional neighbours; tests/t_window.m31
MED_help.m31       ? and which-key content from keymap data
m3d1tor.m31        entry: args, terminal check, tui loop
ui/MED_app.m31  front end (v0.4.0 tui): key translation, render, buffers (:e :ls :b :bn :bp :bd, CTRL-^, `:wa`), mouse (press, drag, wheel), :w/:q, ZZ; tests/t_app.m31
```

## 7. Oracle test plan

Oracle: `nvim --headless -u NONE -i NONE -n -l <driver.lua>`; the driver sets the
buffer lines and cursor, runs `nvim_feedkeys(keys, 'xt', false)` (`x` executes
until the typeahead is empty and ends a pending Insert as if Escape were
typed), then writes JSON: lines, cursor (1-based row, 0-based byte col), mode,
registers `" 0-9 - a-z / : . %` (text + type), marks, the undo sequence number,
and `v:errmsg`. One nvim process per case (about 40 ms) run in a thread pool, so
no state (registers, last search, `.`, jumplist) can leak between cases. nvim's
defaults are part of the contract: `autoindent`, `nostartofline`,
`nojoinspaces`, `shiftwidth=8`, `tabstop=8`, `noexpandtab`, `whichwrap=b,s`,
`iskeyword=@,48-57,_,192-255`, `backspace=indent,eol,nostop`,
`nrformats=bin,hex`, `wrapscan`, `matchpairs=(:),{:},[:]`.

The m31 side is `tests/t_oracle_run.m31`: reads a case file (one case per line
of escaped fields), builds an `Editor`, feeds the key notation, prints the same
fields. Python (`tests/oracles/oracle_nvim.py`) owns case generation, the nvim
run, the m31 run and the comparison, so neither side compares itself with itself.

Compared per case: buffer text, cursor, mode, every register's text and type,
and (corpus level, phase 1.5) marks and undo position. Cursor is compared as byte
column; `curswant` is compared where nvim exposes it (`winsaveview().curswant`).

Layers of cases:

1. **Hand corpus** (`tests/oracles/corpus/*.txt`): grouped by feature
   (motions, operators, text objects, registers, counts, dot, undo/redo, visual,
   ex, search, unicode), every case a `name | text | keys` row. It grows with
   every bug found.
2. **Fuzzer**: deterministic (`--seed N`, `--cases M`); a grammar-aware
   generator picks small texts (1-5 lines from an alphabet of ASCII words,
   punctuation, tabs, blanks, empty lines, and Unicode: accents with combining
   marks, CJK wide characters, emoji ZWJ sequences, RTL), then 1-8 commands from
   the supported feature set (counts, registers, operators with motions and
   objects, visual selections, `u`/`<C-r>`/`.`/macros, `:s` with a
   small pattern set). Only commands the engine claims to support are generated;
   the feature set widens as the engine does.
3. **Shrinker**: on a mismatch, drop keys and text lines while the mismatch
   persists, and print the minimal repro as a corpus row.
4. **Known divergences**: `tests/oracles/known_divergences.txt`, each row names a
   case (or fuzz seed + index), the reason and the nvim behaviour. A listed
   divergence is reported but does not fail; an unlisted one fails; a listed one
   that now matches also fails (stale entry), so the list cannot rot.

The shell side (`tests/test_engine.sh`, sourced by `tests/test.sh`) prints
`N cases, M matched, K known divergences, F failed`.

Also: pure unit tests (`t_*.m31`) for text, keys, fuzzy, undo, and `fmt --check`.

## 8. Benchmark plan (against nvim and hx)

Harness `bench/bench.py` drives each editor in a real pty (python `pty`), with a
scripted key stream and a sentinel to find completion, so all three are measured
the same way. Fixtures are generated deterministically (seeded): 1k-line, 100k-line
and 1M-line source-like files, one 20 MB single-line file, and a large git repo
checkout for the picker.

| Measurement | How | Compared |
|---|---|---|
| startup | spawn → first full frame bytes, 20 runs, median/p95 | nvim `-u NONE`, hx, medit |
| open large file | spawn with 1M-line file → first frame; peak RSS (`VmHWM`) | all |
| search | `/needle<CR>` (rare and common) on 1M lines, time to cursor placed (sentinel `:echo`-equivalent) | nvim, hx (`/`) |
| replace-all | `:%s/a/b/g` on 1M lines (hx has no direct equivalent: `s` + `r`; reported separately) | nvim, medit |
| scroll / redraw | hold `<C-d>`/`<C-f>` 2000 times with a 200 col × 60 row pty; bytes emitted and wall time | all |
| typing | 10k inserted characters in one line and in a 100k-line file | all |
| memory | RSS after load and after 1000 edits with undo history | all |
| picker | files over a 100k-file tree: time to first result, time to settle after each keystroke; fzf as a reference | nvim+fzf-lua if present, hx, medit |

Results go in the benchmark repo (not here); this repo holds the harness. No
numbers are claimed before they are measured. Expectation recorded up front so it
can be checked: medit will lose on large-file load and single-line edits (refcounted
`str` lines, no rope) and should be competitive on small files and the picker.

## 9. v0.1.0 acceptance: "at least as capable as Helix, with Vim bindings"

Helix 25.01 feature inventory and the v0.1.0 verdict. **Yes** = in the tag,
**Partial** = in the tag but narrower, **Later** = after the tag, **Impossible**
= cannot be built in m31 today.

| Helix feature | v0.1.0 | Note |
|---|---|---|
| Modal editing, motions, text objects, counts, registers, macros | Yes | Vim grammar, oracle-tested against nvim |
| Undo tree (`u`, `U`, earlier/later) | Yes | Undo tree with `g-`/`g+`; Vim `u`/`<C-r>` |
| Multiple selections / multi-cursor | **Partial** | Not Helix's selection-first model. Covered by visual block `I`/`A`/`c`, `:s`, `:g`, `:normal`, macros and dot repeat, and (later) `gn`/`cgn` |
| Fuzzy file picker, buffer picker, global search, jumplist picker, last picker | Yes | M3 |
| Command palette | Yes | M3 |
| File explorer | Yes | Picker-based, as in Helix (M4) |
| Which-key style popups for prefixes | Yes | M3 |
| Splits | Yes | M4 |
| Buffers (list, switch, close) | Yes | |
| Git diff gutter | Yes | M4, HEAD vs buffer |
| Auto pairs, comment toggle, surround | Yes | M4 |
| Mouse (click, scroll, drag-select) | Partial | Click/scroll first; drag-select later |
| Clipboard | Partial | Yank via OSC 52 to the terminal clipboard, paste via the terminal's bracketed paste. No `"+p` read-back (G5) |
| Themes | Partial | One dark and one light built in; no per-language scopes |
| Syntax highlighting | **Later** | Lexical highlighter, not tree-sitter |
| Tree-sitter textobjects (`maf`, `mic`), indentation, selection expansion | **Impossible** (G3) | No tree-sitter runtime in m31 and the rule forbids Rust/FFI work |
| LSP: diagnostics, completion, hover, goto, rename, code actions, signature help, inlay hints | **Impossible today** (G1) | Needs piped child stdio |
| Formatting via external formatter, shell pipe (`!`, `\|`, `:pipe`), `:sh`-capture, `:r !cmd` | **Impossible today** (G1) | Same gap; `:!cmd` with inherited terminal works |
| Debug adapter (DAP) | **Impossible today** (G1) | |
| Embedded terminal | **Impossible** (G4) | No pty |
| Soft wrap, rulers, indent guides, whitespace rendering | Later | Rulers and soft wrap are view features, listed for after the tag |
| Snippets | Later | |
| Auto-reload on external change, auto-save | Partial | Poll `fs.stat` mtimes on idle tick; auto-save later |
| Persistent undo, session restore | Later | |
| Increment/decrement (`<C-a>`/`<C-x>`) | Yes | Engine feature, oracle-tested |
| Search (`/`, `?`, `*`, `#`), `:s`, `:g` | Yes | Vim regex subset; no backreferences or lookaround in the regex engine (G6) |
| Config file | Yes (minimal) | `~/.config/medit/keymap` + options; no scripting |

Honest summary: with Vim bindings, medit can match or exceed Helix on
editing, navigation, picker and window features. It cannot match Helix on the
three things built on external-process or parser infrastructure: LSP, tree-sitter
and shell pipes, and it will not until the runtime supplies process pipes and
(for tree-sitter) a parser strategy. A v0.1.0 that omits those is "capable
as Helix without its language intelligence", and the tag description must say so.

## 10. Milestones

* M0 (this commit): design and scaffolding.
* M1: engine + oracle harness + fuzzer, with a stated divergence list.
* M2 (started: `m3d1tor <file>` opens, renders with gutter and status line, edits, `:w`, `:q`, `ZZ`; build with `scripts/build.sh`): tui integration: render, scroll, numbers, statusline, command line, insert
  entry, open/save, grapheme width.
* M3 (done): pickers (files, buffers, grep, commands, help, explorer), which-key, keymap help.
  Deviations from section 4: sources run synchronously on the loop (the file list
  and grep corpus are cached; grep is debounced 120 ms by the ticker), not on a
  spawned thread; `?` stays Vim's backward search, so the keymap help is
  `<Space>?` / `:help`; Space is the leader in Normal mode (it no longer moves
  right); which-key only exists for the leader, not for `g`/`z`; no `<C-q>`
  quickfix list yet; the buffers picker is in buffer order, not MRU. There is no
  nvim oracle for buffers and pickers, so they are covered by unit tests and
  manual runs only.
* M4 (in progress): splits are done (`:split :vsplit :new :vnew :close :only :wincmd`, `<C-w>` s v n c q o w W p t b h j k l, `<Space>sv/sh/se/sc/o/n`, mouse click focuses a window). Windows split the space equally (no `:resize` or `<C-w>+-<>|`, `<C-w>=` is a no-op); each has its own status line and shows its own cursor and view of a shared buffer; closing a window keeps its buffer loaded (hidden), so `:q` of a modified buffer in a window never prompts, and E162 reports it at the final quit. Edits made through one window do not move the cursor of another window on the same buffer (it is only clamped). Not done: `<C-w>HJKLrRx` (move/rotate/exchange windows), counts for `<C-w>`.
* M4 explorer: done. `<Space>e` / `<Space>fe` is the picker explorer (`-` up on an empty prompt). `:Explore [dir]`, `:Sexplore`, `:Vexplore` and `:e dir` open a read-only directory buffer (`../`, folders, files; cursor on the file we came from): Enter opens the entry (the listing buffer is dropped when a file replaces it), `-` goes up, and any edit is undone at once by re-reading the directory with Vim's E21; `:w` gives E382. Not done: netrw's rename/delete/create keys, `gh` hidden toggle (dotfiles are always shown, `.git` never). In every picker CTRL-S / CTRL-V accept a file, buffer or grep hit into a new window below / beside.
* M4 (before the tag): git gutter, surround/comment/autopairs,
  marks UI, keymap file, benchmarks run and recorded.

## 11. m31 gaps (stop-and-report items, not worked around)

| # | Gap | Effect |
|---|---|---|
| G1 | `os.run` inherits stdio; no way to pipe a child's stdin/stdout | No LSP, DAP, filters, `:r !cmd`, formatter via stdin/stdout. Needs a runtime change |
| G2 | No SIGWINCH / signals | Resize is polled each tick (works; slightly delayed) |
| G3 | No tree-sitter or foreign-library binding | No parse-tree features |
| G4 | No pty | No embedded terminal |
| G5 | No clipboard read, no process pipe to `wl-copy`/`xclip` | OSC 52 yank only |
| G6 | `regex` has no backreferences/lookaround, `\d \w \s` ASCII-only | Vim `\1`, `\@=` etc. unsupported in `:s`/search |
| G7 | `str` immutable, no function values, `match` only on enums | Design choices above (line array, enum dispatch); not blockers |
| G8 | **Miscompile** (m31c 0.3.3 `--emit-c`, -O2): when both arms of an `if`/`else` start with the same assignment, that assignment is dropped. Repro: `int b(int x, bool open) { int i = x; int f = 0; if (open) { f = i; i = 1; } else { f = i; i = 2; } return f * 1000 + i; } print(b(40, true).to_str());` prints `1`, expected `40001` | Worked around by hoisting the shared assignment above the `if` (MED_search.findmatch). Needs a compiler fix |
