# Changelog

## 0.5.0

Themes. The hard-wired mapping onto the terminal's 16 colours is gone; every colour the renderer draws now comes from a
theme, a Helix-format TOML file (`[palette]`, scope to style, `inherits`).

- Fourteen built-in themes compiled into the binary: `default` (a new dark theme, truecolor, transparent background),
  `default-light`, `term16-dark` / `term16-light` (the terminal's own 16 colours, used instead of the defaults on
  16-colour terminals), and the Helix ports of `tokyonight` (night), `nightfox`, `gruvbox-material` (dark, medium) and
  `-soft`, `gruvbox`, `catppuccin-mocha`, `onedark`, `nord`, `dracula`, `github-light`. Sources are `themes/*.toml`;
  `scripts/gen_themes.sh` embeds them in `ui/MED_theme_data.m31`.
- `:theme` (shows the current theme), `:theme NAME` and `:colorscheme NAME` switch at once; Tab completes names;
  `<Space>fC` is a picker that previews each theme as the selection moves and goes back on Esc; `--theme NAME`;
  `colorscheme NAME` in the startup file (`keymap.vim`). `:set background=light|dark` still moves between `default` and
  `default-light`. A bad theme is a message and the old theme stays.
- User themes: `~/.config/m3/themes/NAME.toml` (`$XDG_CONFIG_HOME`), shadowing or inheriting built-ins. All 154 themes
  of Helix 25.01 load.
- Scope lookup falls back by dotted prefix as in Helix, then through the names Helix themes do have for the scopes m3
  adds (`ui.statusline.visual`, `ui.which-key`, `ui.picker.*`, `search.match`, ...). All 25 `syntax` classes have a
  scope (`SYN_class.legacy`, the fold onto 12, is no longer used by the renderer). Statusline mode colours, git gutter,
  signs, which-key, picker, tab line, indent guides, cursor line, colour columns, selection, search, TODO highlight and
  the tree all go through scopes; a theme with `ui.background` paints the whole screen, one without leaves the
  terminal's background alone.
- Colours are written at the terminal's depth (truecolor, the 256 cube, or the nearest of 16).
- `m3 --dump-sample [--theme NAME] [--colors 16|256|true]` draws sample code in six languages, the theme picker and the
  which-key popup through the real renderer as ANSI text.
- `:source` now runs requests that a sourced file queues (`:theme` lines) before the next key.
- Tests: `tests/t_theme.m31` (parser, palettes, inheritance, fallback, depth, every built-in, user themes in a temporary
  XDG directory, bad themes, the commands, the picker, `--dump-sample`; it reads the renderer's source and fails when a
  built-in lacks a scope the renderer asks for), a pty scenario `themes` in `tests/e2e.py`.

Not done: underline colour and curl (the `tui` style has six attribute bits and no underline colour), blink and hidden
modifiers, diagnostic underlines in the text (only the sign column shows diagnostics), per-heading-level markdown
colours (the lexical highlighter has one heading class), a theme setting saved from the picker.

## 0.4.0

A round of queue items, each probed against nvim where the repo can.

- Tab pages: `:tabnew :tabedit :tabnext :tabprev :tabNext :tabfirst :tablast :tabclose :tabonly :tabmove :tabs`,
  `gt` / `gT`, `<C-w>T`, a tab line, a layout per page. `:q`, `:close` and `<C-w>c` on the last window of a page close
  the page.
- Command-line abbreviations (`:cabbrev :cnoreabbrev :cunabbrev :cabclear`); `:ab` is now Insert and command line;
  `:unabbreviate` arguments are not expanded; end-id and non-id left-hand sides are not recognised straight after
  punctuation (Insert mode too); `:ab` lists in nvim's format. Corpus 105.
- Windows follow nvim's frame model (see the README): halves, equalising after a split or close, 'winwidth',
  `:resize` and `<C-w> + - < > _ |` taking rows from the next windows first, terminal resizes shrinking the last
  window first, counts after `<C-w>`, `<C-w>x r R H J K L` as `win_exchange` / `win_rotate` / `win_totop`.
  `tests/oracles/oracle_windows.py` (115 cases plus random sequences) is part of `tests/test.sh`.
- LSP: signature help, inlay hints, `textDocument/didClose`; the scripted fake server grew the three methods.
- Marks, registers and macros, from a probe of 480 cases (corpus 106): `]'` `['` `` ]` `` `` [` ``, `]p [p ]P [P`,
  the expression register `"=` and `:put =`, `:let @A=`, `:let @"=`, the unnamed register reading register 0 before
  anything is written, the `.` mark and change list after put, join, linewise delete, shift, `:copy`, `:move`,
  `:s` over several lines, a character-wise multi-line delete, a block delete or insert and undo / redo (`g;` and
  `` `. `` land where nvim's do), the `<` and `>` marks after their lines are deleted, `E19` for a mark below the end.
- Git gutter: already in place (an in-repo diff against the index or HEAD blob; no `gitui` dependency needed); tests added
  for `]c` / `[c`, no repository and a 100000-line file.

- File-name completion sorts a directory by its name, not by the `/` after it (`next` before `next-2`).

Known gaps: text typed in one burst leaves `.` at its last character, nvim at its first (nvim's typeahead
batching); `gq` leaves `.` one line higher; resizing the only window, or a column that is the whole screen, does not
grow the command line as nvim does;
`:tab` as a modifier (`:tab split`), `:{N}tabnew` placement; inlay hints are drawn at the end of the line, not inline.

## 0.3.0

Chosen from probing the engine against nvim for gaps (a batch of 110 ad hoc daily-use cases; the failures became this
release) and from the 0.2.0 note that the renderer still folded the library's classes onto twelve.

- Insert-mode abbreviations (`:ab :iab :noreab :inoreab :unab :iunab :abc :iabc`), checked against nvim (corpus 104).
- `:let` variables (`g:` scope, `+= -= *= .=`) usable in `\=` and `:echo`; `\=` with a variable matched nvim.
- Richer highlighting: the renderer draws every class of the `syntax` library instead of folding onto twelve.
- `gw` keeps the cursor on blank text through a join and when nothing changes (it moved one column).
- A command that changes nothing (`x` on an empty line) no longer enters the change list or sets the `.` mark, so
  `g;` and `` `. `` match nvim.

Known gaps: abbreviations in the command line, non-id abbreviations expand only on `<Esc>`/`<CR>`/`CTRL-]`,
tab pages (`:tabnew`), `:ab` listing format, `gw` cursor after a re-wrap that moves it to another line.

## 0.2.0

Highlighting by the shared `syntax` library (see RENAMES.md).
