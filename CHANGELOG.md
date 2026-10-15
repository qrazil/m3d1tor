# Changelog

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
