# medit

A terminal text editor with Vim key bindings, written in
[m31](https://github.com/qrazil/m31) on the [tui](https://github.com/qrazil/tui)
library. IDE-lite: keyboard first, no toolbar or menu chrome, discoverable
through which-key, a command palette and `?`.

Status: pre-0.1, under construction. See `DESIGN.md` for the plan, the plugin
decision table, the architecture and what v0.1.0 means.

The editing engine is tested differentially against `nvim --headless`.

## Build and test

    M31_ROOT=/path/to/m31 LANGC=/path/to/m31c bash scripts/build.sh
    M31_ROOT=/path/to/m31 LANGC=/path/to/m31c bash tests/test.sh

Needs `nvim` (0.11) and `python3` for the oracle tests.
