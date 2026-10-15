# 0.2.0: highlighting by the shared `syntax` library

| old | new |
|---|---|
| `engine/MED_syntax.m31` (`MED_syntax.language_of`, `classify`, `languages`, the class constants) | the `syntax` dependency: `SYN_detect.language_of`, `SYN_highlight`, `SYN_registry.names`, `SYN_class` |
| 12 languages | 77 (`:set syntax=` takes any of `SYN_registry.names()` or an alias) |
| `Editor.syn_lang`, `syn_states`, `syn_valid` | `Editor.syn`, a `SYN_highlight.Highlighter` |
| `MED_app.comment_for` extension lists | the library's comment forms for the detected language |
| markdown fence marker is SPECIAL, `#include` is PREPROC | the library classes them RAW (drawn as a string) and KEYWORD |
| a `.ts` file is language `javascript` | language `typescript` (the language server is still shared); `--version` is `m3 0.2.0` |

# 0.1.0: m3d1tor is now m3dit, the command is `m3`

| old | new |
|---|---|
| repository `qrazil/m3d1tor` | `qrazil/m3dit` (GitHub redirects the old URL) |
| binary `m3d1tor` | `m3` (short, like `vi` / `nvim` / `hx`) |
| entry file `m3d1tor.m31` | `m3.m31` |
| project `name m3d1tor` in `deps` | `name m3dit` |
| release assets `m3d1tor-<os>-<arch>.tar.gz` | `m3-linux-x86_64.tar.gz`, `m3-linux-aarch64.tar.gz`, `m3-macos-arm64.tar.gz` (same layout inside, binary named `m3`) |
| `~/.config/m3d1tor/keymap.vim` | `~/.config/m3/keymap.vim` (the old file is still read when the new one is absent) |
| `~/.local/state/m3d1tor` | `~/.local/state/m3` (old state files are read until the new ones are written) |
| `M3D1TOR_KEYMAP`, `M3D1TOR_NO_MOUSE`, `M3D1TOR_CLIP_COPY`, `M3D1TOR_CLIP_PASTE` | `M3_KEYMAP`, `M3_NO_MOUSE`, `M3_CLIP_COPY`, `M3_CLIP_PASTE` |
| `--version` output `m3d1tor 0.0.x` | `m3 0.1.0` |

Why: a short binary name that is quick to type, and a readable repository name.
The 0.0.1 to 0.0.3 pre-releases were published as `m3d1tor`; those tags and
assets keep that name.

The `MED_` module prefix is unchanged: it stands for "m3 edit" (earlier "medit"),
so no module, type or function was renamed.

# Grouped layout (0.0.x)

**No module, type, function or field changed its name.** The `MED_` prefix and
every name stay. Only file locations and import paths changed: `engine/` holds
the editing core, `ui/` holds drawing, input and navigation, `m3d1tor.m31`
stays at the root. `deps` says version 0.0.2: the first published release (0.0.1 was never published: its
release build failed on a call to a function that does not exist, `io.print`, in the entry file
that no test compiled; `tests/test_entry.sh` now builds and runs the real binary on every platform). v0.1.0
acceptance (DESIGN section 9) is not met, so every release stays a pre-release.

v0.0.2, first published release: what works is listed in README.md (Status and Features);
the known limits are listed there too and in `tests/oracles/known_divergences.txt`.

| old file / import | new file / import |
|---|---|
| `MED_buffer.m31` / `import MED_buffer;` | `engine/MED_buffer.m31` / `import engine.MED_buffer;` |
| `MED_text` | `engine/MED_text` |
| `MED_charclass` | `engine/MED_charclass` |
| `MED_case` | `engine/MED_case` |
| `MED_key` | `engine/MED_key` |
| `MED_parse` | `engine/MED_parse` |
| `MED_num` | `engine/MED_num` |
| `MED_nrfmt` | `engine/MED_nrfmt` |
| `MED_motion` | `engine/MED_motion` |
| `MED_textobj` | `engine/MED_textobj` |
| `MED_register` | `engine/MED_register` |
| `MED_regex` | `engine/MED_regex` |
| `MED_search` | `engine/MED_search` |
| `MED_editor` | `engine/MED_editor` |
| `MED_ex` | `engine/MED_ex` |
| `MED_vim` | `engine/MED_vim` |
| `MED_view` | `engine/MED_view` |
| `MED_app` | `ui/MED_app` |
| `MED_keymap` | `ui/MED_keymap` |
| `MED_window` | `ui/MED_window` |
| `MED_picker` | `ui/MED_picker` |
| `MED_picker_view` | `ui/MED_picker_view` |
| `MED_fuzzy` | `ui/MED_fuzzy` |
| `MED_files` | `ui/MED_files` |
| `MED_grep` | `ui/MED_grep` |
| `MED_ignore` | `ui/MED_ignore` |

## tui 0.5.0

`deps` now pins `tui` 5327361 (v0.5.0 plus drain_events), which moved its modules into folders, so
the tui imports changed with it (same modules, see tui's RENAMES.md):

| old | new |
|---|---|
| `import tui.TUI_app;` | `import tui.app.TUI_app;` |
| `import tui.TUI_buffer;` `TUI_geometry` `TUI_style` `TUI_text` `TUI_widget` `TUI_mouse` | `import tui.core.TUI_buffer;` ... |
| `import tui.TUI_menu;` | `import tui.widgets.TUI_menu;` |

## Other changes

- `tests/test.sh` is the single entry (unchanged path); the generators in
  `tests/oracles/` now write `engine/MED_case.m31` and `engine/MED_charclass.m31`.
- `.github/workflows/release.yml` is new (tag-triggered, 3 platforms, test precondition).
- The README is rewritten; `DESIGN.md` is kept, its module list shows the new paths.
