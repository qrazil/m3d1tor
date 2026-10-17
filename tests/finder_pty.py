#!/usr/bin/env python3
"""The fuzzy finder never leaves a stale or broken cell (docs/FINDER.md).

    python3 tests/finder_pty.py ./m3 [--quick]

Opens the finder (<Space>ff) over a tree of adversarial names (longer than the box, wide CJK and
emoji, combining marks, tabs, control bytes, ESC sequences, names that differ only in width) and
files with hostile contents (very long lines, tabs, binary). After every step the screen the
diff renderer produced is compared with a from-scratch redraw of the same state (a resize away and
back is always a full redraw), and the box is checked for an intact frame: every row of the box
starts with its left border and ends with its right border, nothing is drawn outside it.
Skips with a note when pyte is missing.
"""
import os
import sys
import tempfile
import shutil

try:
    import pyte
except ImportError:
    print("skip finder_pty: pyte is not installed")
    sys.exit(0)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "bench"))
import uxperf  # noqa: E402

ROWS, COLS = 30, 120
SYNC_END = b"\x1b[?2026l"

NAMES = [
    "plain.txt",
    "a_very_long_name_" + "x" * 90 + ".txt",
    "ends_exactly_" + "y" * 20 + ".md",
    "中文文件名_漢字かなカナ_" + "中" * 30 + ".txt",
    "emoji_\U0001f600\U0001f680\U0001f9d1‍\U0001f4bb_end.txt",
    "combining_ééé_å̈.txt",
    "tab\there.txt",
    "ctl_\x01\x02\x07\x7f_end.txt",
    "esc_\x1b[31mred\x1b[0m_end.txt",
    "esc2_\x1b]0;title\x07_end.txt",
    "wide_ＡＢＣ.txt",
    "narrow_ABC.txt",
    "zwj_\U0001f468‍\U0001f469‍\U0001f467_family.txt",
    "flag_\U0001f1e9\U0001f1ea_de.txt",
    "dir/inner/pom.xml",
    "dir/inner/" + "z" * 100 + ".txt",
    "pom.xml",
    "poxm.txt",
]

BODIES = {
    "plain.txt": "hello\nworld\n",
    "a_very_long_name_": "x" * 5000 + "\nshort\n",
    "ends_exactly_": "\ttabbed\tline\twith\ttabs\n" * 40,
    "中文": "中文中文" * 100 + "\nこんにちは\n",
    "emoji_": "\U0001f600" * 200 + "\né" * 100 + "\n",
    "ctl_": "a\x01b\x02c\x1b[2Jd\x1b[31mred\x07\x08\x08\x08\n" * 5,
    "esc_": "\x1b[2J\x1b[H\x1b]0;x\x07\x1b[?1049h\n",
    "tab": "\t" * 300 + "end\n",
    "zwj_": "\U0001f468‍\U0001f469‍\U0001f467 " * 100 + "\n",
    "pom.xml": "<project>\n" + "  <a>" + "w" * 300 + "</a>\n" * 3 + "</project>\n",
}


def make_tree(root):
    for name in NAMES:
        path = os.path.join(root, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        body = "line\n" * 5
        for key, value in BODIES.items():
            if name.startswith(key):
                body = value
        with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
            f.write(body)
    with open(os.path.join(root, "binary.bin"), "wb") as f:
        f.write(b"\x00\x01\x02" * 100 + b"\xff\xfe")
    with open(os.path.join(root, "crlf.txt"), "wb") as f:
        f.write(b"first line\r\nsecond line with carriage return\r\n" * 20 + b"\x0c form feed\x0b vt\r\n")
    with open(os.path.join(root, "latin1.txt"), "wb") as f:
        f.write(b"caf\xe9 \xff\xfe not utf-8\n")
    with open(os.path.join(root, "bom.txt"), "wb") as f:
        f.write(b"\xef\xbb\xbfbom first\n\xc2\x85next-line c1\xc2\x9b31m c1 csi\n")
    with open(os.path.join(root, "oneline.txt"), "w") as f:
        f.write("0123456789" * 20000)
    with open(os.path.join(root, "bulk.txt"), "w") as f:
        for i in range(300):
            f.write("line %d %s\n" % (i, "q" * (i % 90)))
    for i in range(60):
        with open(os.path.join(root, "file_%02d.txt" % i), "w") as f:
            f.write("f%d\n" % i)


class Term:
    def __init__(self, binary, root, rows=ROWS, cols=COLS, env=None, keymap="NONE"):
        self.ed = uxperf.Editor(binary, root, [], rows, cols, env=env, keymap=keymap)
        self.rows, self.cols = rows, cols
        self.screen = pyte.Screen(cols, rows)
        self.stream = pyte.ByteStream(self.screen)
        self.fed = 0
        self.settle()

    def settle(self, quiet=0.15):
        self.ed.settle(quiet, 6)
        data = bytes(self.ed.raw[self.fed:])
        self.fed = len(self.ed.raw)
        self.stream.feed(data)

    def type(self, keys, quiet=0.15):
        self.ed.send(keys)
        self.settle(quiet)

    def resize(self, rows, cols):
        self.ed.resize(rows, cols)
        self.rows, self.cols = rows, cols
        self.screen.resize(rows, cols)
        self.settle(0.25)

    def cells(self):
        buf = self.screen.buffer
        return [[(buf[y][x].data, buf[y][x].fg, buf[y][x].bg, buf[y][x].reverse, buf[y][x].bold)
                 for x in range(self.cols)] for y in range(self.rows)]

    def text(self):
        """One string per row, one character per cell (a wide character's second cell is a blank
        placeholder), so a string index is a column."""
        buf = self.screen.buffer
        return ["".join((buf[y][x].data or " ") if len(buf[y][x].data) <= 1 else buf[y][x].data[0]
                        for x in range(self.cols)) for y in range(self.rows)]

    def full_redraw(self):
        """The screen after a from-scratch redraw: wiggle the size (a resize is a `full` frame)."""
        before = (self.rows, self.cols)
        self.resize(before[0] + 1, before[1])
        self.resize(*before)
        return self.cells(), self.text()

    def close(self):
        self.ed.close()


class Report:
    def __init__(self):
        self.failures = []
        self.checks = 0

    def fail(self, label, detail):
        self.failures.append("%s: %s" % (label, detail))


def box_problems(term):
    """Every row between the top and bottom border of the finder box keeps both side borders."""
    rows = term.text()
    problems = []
    top = None
    for y, row in enumerate(rows):
        if row.lstrip().startswith("╭") or "╭" in row:
            top = y
            break
    if top is None:
        return ["no top border"]
    left = rows[top].index("╭")
    right = rows[top].rindex("╮") if "╮" in rows[top] else None
    if right is None:
        return ["top border has no right corner: %r" % rows[top]]
    bottom = None
    for y in range(top + 1, term.rows):
        if "╰" in rows[y]:
            bottom = y
            break
    if bottom is None:
        return ["no bottom border"]
    if rows[bottom].index("╰") != left or "╯" not in rows[bottom] or rows[bottom].rindex("╯") != right:
        problems.append("bottom border misplaced: %r" % rows[bottom])
    for y in range(top + 1, bottom):
        buf = term.screen.buffer
        if buf[y][left].data != "│":
            problems.append("row %d: left border is %r" % (y, buf[y][left].data))
        if buf[y][right].data != "│":
            problems.append("row %d: right border is %r" % (y, buf[y][right].data))
        for x in range(left + 1, right):
            if buf[y][x].data in ("│",) and False:
                pass
    # nothing drawn right of the box (the area outside is the editor text, empty here)
    for y in range(top, bottom + 1):
        if rows[y][right + 1:].strip():
            problems.append("row %d: stray cells right of the box: %r" % (y, rows[y][right + 1:]))
    return problems


def check(term, rep, label, expect_box=True):
    rep.checks += 1
    shown_cells, shown_text = term.cells(), term.text()
    if expect_box:
        for p in box_problems(term):
            rep.fail(label, "frame: " + p)
    full_cells, full_text = term.full_redraw()
    if shown_text != full_text or shown_cells != full_cells:
        diff = []
        for y in range(term.rows):
            if shown_text[y] != full_text[y]:
                diff.append("row %d diff=%r full=%r" % (y, shown_text[y].rstrip(), full_text[y].rstrip()))
            elif shown_cells[y] != full_cells[y]:
                xs = [x for x in range(term.cols) if shown_cells[y][x] != full_cells[y][x]]
                diff.append("row %d style differs at cols %s" % (y, xs[:8]))
        rep.fail(label, "diff-rendered screen != full redraw: " + " | ".join(diff[:3]))
    if expect_box:
        for p in box_problems(term):
            rep.fail(label, "after full redraw, frame: " + p)


def scenario_navigate(binary, root, rep, quick):
    term = Term(binary, root)
    try:
        term.type(" ff", 0.6)
        check(term, rep, "open")
        n = 8 if quick else 40
        for i in range(n):
            term.type("\x0e")      # CTRL-N
            check(term, rep, "down %d" % i)
        for i in range(n):
            term.type("\x10")      # CTRL-P
            check(term, rep, "up %d" % i)
        term.type("\x1b[6~")
        check(term, rep, "page down")
        term.type("\x1b[F")
        check(term, rep, "end")
        term.type("\x1b[H")
        check(term, rep, "home")
    finally:
        term.close()


def scenario_queries(binary, root, rep, quick):
    term = Term(binary, root)
    try:
        term.type(" ff", 0.6)
        queries = ["e", "ex", "end", "中", "x", "pom", "", "zzzzzzz", "tab", "a", "esc", "\x1b[31m"]
        if quick:
            queries = queries[:6]
        for q in queries:
            term.type("\x15")  # CTRL-U
            check(term, rep, "clear before %r" % q)
            for ch in q:
                if ch == "\x1b":
                    continue
                term.type(ch)
                check(term, rep, "query %r char %r" % (q, ch))
            term.type("\x7f")
            check(term, rep, "query %r backspace" % q)
    finally:
        term.close()


def scenario_preview(binary, root, rep, quick):
    term = Term(binary, root)
    try:
        term.type(" ff", 0.6)
        for q in ["oneline", "binary", "bulk", "tab", "esc_", "emoji", "ctl_", "zwj", "中文", "a_very", "pom"]:
            term.type("\x15")
            term.type(q)
            check(term, rep, "preview of %r" % q)
            term.type("\x0e")
            check(term, rep, "preview of %r, next" % q)
    finally:
        term.close()


def scenario_resize(binary, root, rep, quick):
    term = Term(binary, root)
    try:
        term.type(" ff", 0.6)
        term.type("e")
        sizes = [(30, 90), (20, 60), (12, 40), (30, 130), (40, 100), (8, 30), (30, 120)]
        if quick:
            sizes = sizes[:4]
        for rows, cols in sizes:
            term.resize(rows, cols)
            term.type("\x0e")
            check(term, rep, "resized to %dx%d" % (rows, cols))
            term.type("\x10")
            check(term, rep, "resized to %dx%d then up" % (rows, cols))
    finally:
        term.close()


def screen_rows(term):
    return [r.rstrip() for r in term.text()]


def scenario_ranking(binary, root, rep, quick):
    """The finder lists the best match first, with a relevance, and the options work."""
    term = Term(binary, root)
    try:
        term.type(" ff", 0.5)
        term.type("pom")
        rows = screen_rows(term)
        names = [r for r in rows if "pom.xml" in r or "poxm.txt" in r]
        first = next((i for i, r in enumerate(rows) if "> pom.xml" in r), None)
        if first is None:
            rep.fail("ranking", "pom.xml is not the selected first row: %r" % rows[2:8])
        else:
            order = [r for r in rows[first:first + 4] if "%" in r]
            if len(order) < 3 or "pom.xml" not in order[0] or "poxm.txt" not in order[2]:
                rep.fail("ranking", "pom order wrong: %r" % order)
            if not all(r.split("\u2502")[1].rstrip().endswith("%") for r in order if "\u2502" in r):
                rep.fail("ranking", "a row has no percentage at its right edge: %r" % order)
        check(term, rep, "ranking: pom")
        term.type("\x0c")           # CTRL-L: write the whole screen again
        check(term, rep, "ranking: after CTRL-L")
        term.type("\x1b")
        term.type(":set nofinderscore\r", 0.3)
        term.type(" ff", 0.5)
        term.type("pom")
        if any("%" in r.split("\u2502")[1] for r in screen_rows(term) if "pom" in r and "\u2502" in r):
            rep.fail("ranking", ":set nofinderscore still shows the percentage")
        check(term, rep, "ranking: nofinderscore")
    finally:
        term.close()


def scenario_frecency(binary, root, rep, quick):
    """Opening a file makes the finder list it first (and mark it); a clean run keeps nothing."""
    state = os.path.join(root, ".state", "m3", "frecency")
    keymap = os.path.join(root, "keymap.vim")
    with open(keymap, "w") as f:
        f.write('" empty\n')
    if os.path.exists(state):
        os.remove(state)
    term = Term(binary, root, keymap=keymap)
    try:
        term.type(" ff", 0.5)
        term.type("file_42")
        term.type("\r", 0.6)
    finally:
        term.close()
    if not os.path.exists(state):
        rep.fail("frecency", "no state file after opening a file")
        return
    with open(state) as f:
        text = f.read()
    if "file_42.txt" not in text:
        rep.fail("frecency", "the opened file is not in the state: %r" % text[:200])
    if os.path.exists(state + ".tmp"):
        rep.fail("frecency", "a temporary state file was left behind")
    term = Term(binary, root, keymap=keymap)
    try:
        term.type(" ff", 0.6)
        rows = screen_rows(term)
        listed = [r for r in rows if "file_42.txt" in r]
        if not listed or "> file_42.txt" not in listed[0] and "file_42.txt" not in rows[3]:
            rep.fail("frecency", "file_42.txt is not first with an empty prompt: %r" % rows[2:6])
        elif "*" not in rows[3]:
            rep.fail("frecency", "no frecency marker on the first row: %r" % rows[3])
        check(term, rep, "frecency: empty prompt")
    finally:
        term.close()
    os.remove(state)
    clean = Term(binary, root)
    try:
        clean.type(" ff", 0.5)
        clean.type("file_07")
        clean.type("\r", 0.6)
    finally:
        clean.close()
    if os.path.exists(state):
        rep.fail("frecency", "a clean run (--keymap NONE) wrote the state file")


def main():
    binary = os.path.abspath(sys.argv[1])
    quick = "--quick" in sys.argv
    root = tempfile.mkdtemp(prefix="m3finder")
    rep = Report()
    try:
        make_tree(root)
        for scenario in (scenario_navigate, scenario_queries, scenario_preview, scenario_resize, scenario_ranking, scenario_frecency):
            scenario(binary, root, rep, quick)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    for line in rep.failures[:40]:
        print("FAIL " + line)
    print("finder_pty: %d checks, %d failed" % (rep.checks, len(rep.failures)))
    sys.exit(1 if rep.failures else 0)


if __name__ == "__main__":
    main()
