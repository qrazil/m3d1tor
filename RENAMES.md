# Grouped layout (0.0.x)

**No module, type, function or field changed its name.** The `MED_` prefix and
every name stay. Only file locations and import paths changed: `engine/` holds
the editing core, `ui/` holds drawing, input and navigation, `m3d1tor.m31`
stays at the root. The `version` in `deps` is unchanged (no release is tagged;
v0.1.0 acceptance, DESIGN section 9, is not met).

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

`deps` now pins `tui` 1609d91 (v0.5.0), which moved its modules into folders, so
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
