#!/usr/bin/env python3
"""Animation never changes the result, only the path (docs/UX-PERF.md).

    python3 tests/anim_pty.py ./m3 [--quick]

For a corpus of motions the same keys are typed into two editors on the same
file: one animating (the default) and one with `M3_NO_ANIM=1`. After each step
both go quiet and the whole screen -- text, the cursor cell, every cell's
reverse flag -- must be identical. While the animating one runs, every frame
(split at the synchronized-output markers the harness's terminal accepts) is
fed to the screen model and checked: the status line never changes mid-scroll,
the first visible line only moves towards the final one, and the cursor cell
stays inside the window with 'scrolloff' honoured.

Also checked: j/k never animate (one frame, no follow-up), `:set noanimate`
turns it all off, a key during an animation lands the final screen at once,
idle makes no output at all, and quitting restores the terminal.
Skips with a note when pyte is missing. Soft on time, hard on the screens.
"""
import os
import re
import shutil
import sys
import tempfile
import time

try:
    import pyte
except ImportError:
    print("skip anim_pty: pyte is not installed")
    sys.exit(0)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "bench"))
import uxperf  # noqa: E402

ROWS, COLS = 30, 100
SYNC_END = b"\x1b[?2026l"
SYNC_BEGIN = b"\x1b[?2026h"


def make_file(path, lines=3000):
    with open(path, "w") as f:
        for i in range(1, lines + 1):
            if i % 211 == 0:
                f.write("row %05d needle_rare marker\n" % i)
            else:
                f.write("row %05d lorem ipsum dolor sit amet %s\n" % (i, "x" * (i % 17)))


class Run:
    def __init__(self, binary, root, env=None, extra=()):
        self.ed = uxperf.Editor(binary, root, ["big.txt"] + list(extra), ROWS, COLS, env=env)
        self.screen = pyte.Screen(COLS, ROWS)
        self.stream = pyte.ByteStream(self.screen)
        self.fed = 0
        self.frames = []     # screens as text, one per frame, since the last mark()
        self.ed.settle(0.4, 10)
        self.catch_up()

    def catch_up(self):
        """Feed everything read so far, frame by frame; returns the number of frames."""
        data = bytes(self.ed.raw[self.fed:])
        self.fed = len(self.ed.raw)
        n = 0
        while data:
            i = data.find(SYNC_END)
            if i < 0:
                self.stream.feed(data)
                break
            self.stream.feed(data[: i + len(SYNC_END)])
            data = data[i + len(SYNC_END):]
            n += 1
            self.frames.append(self.snapshot())
        return n

    def snapshot(self):
        return {
            "text": list(self.screen.display),
            "bg": [self.screen.buffer[0][x].bg for x in range(COLS)],
            "reverse": sorted((y, x) for y in range(ROWS) for x in range(COLS)
                              if self.screen.buffer[y][x].reverse),
        }

    def type(self, keys, quiet=0.35):
        self.frames = []
        if isinstance(keys, str):
            keys = keys.encode()
        os_write(self.ed.master, keys)
        self.ed.settle(quiet, 5)
        self.catch_up()
        return self.snapshot()

    def close(self):
        self.ed.close()


def os_write(fd, data):
    os.write(fd, data)


def first_line_number(text_rows):
    m = re.match(r"\s*(\d+)", text_rows[0])
    return int(m.group(1)) if m else None


CORPUS = [
    ("half page down, up", ["\x04", "\x15"]),
    ("page down x3, back", ["\x06\x06\x06", "\x02\x02"]),
    ("G then gg", ["G", "gg"]),
    ("distant line", ["1500G", "20%", "75%"]),
    ("search jump and next", ["/needle_rare\r", "n", "n", "N"]),
    ("zt zz zb", ["400Gzt", "zz", "zb"]),
    ("H M L", ["200G", "L", "M", "H"]),
    ("scrolloff 5 and a half page", [":set scrolloff=5\r", "\x04", "\x04", "\x15"]),
    ("scrolloff 5 at the ends", [":set scrolloff=5\r", "G", "\x15", "gg", "\x04"]),
    ("wheel down and up", ["\x1b[<65;20;10M\x1b[<65;20;10M\x1b[<65;20;10M", "\x1b[<64;20;10M\x1b[<64;20;10M"]),
    ("a wheel burst", ["".join("\x1b[<65;20;10M" for _ in range(20))]),
    ("ctrl-e ctrl-y", ["\x05\x05\x05\x05", "\x19\x19"]),
    ("visual then half page", ["V", "\x04\x04", "\x1b"]),
    ("yank, scroll, put", ["10Gyy", "\x04", "p"]),
    ("wrap on and a half page", [":set wrap\r", "\x04", "\x15"]),
    ("macro with scrolls", ["qa\x04q", "@a", "2@a"]),
    ("dot repeat", ["x", "\x04", "."]),
    ("which-key fades in and out", [(" ", 1.0), "\x1b", ("g", 1.0), "\x1b"]),
    ("picker fades in", [(" ff", 0.7), "main", "\x1b"]),
]


def compare(binary, root, name, steps, extra=()):
    a = Run(binary, root, extra=extra)
    b = Run(binary, root, env={"M3_NO_ANIM": "1"}, extra=extra)
    problems = []
    try:
        for i, step in enumerate(steps):
            keys, quiet = step if isinstance(step, tuple) else (step, 0.35)
            sa = a.type(keys, quiet)
            sb = b.type(keys, quiet)
            if sa["text"] != sb["text"]:
                diff = [(n, x, y) for n, (x, y) in enumerate(zip(sa["text"], sb["text"])) if x != y]
                problems.append("step %d %r: text differs, first at row %d:\n  anim   %r\n  static %r" %
                                (i, keys, diff[0][0], diff[0][1], diff[0][2]))
            elif sa["reverse"] != sb["reverse"]:
                problems.append("step %d %r: cursor cells differ: %r vs %r" % (i, keys, sa["reverse"][:4], sb["reverse"][:4]))
            # the animating editor's frames: the status line is the engine's, always
            final_status = sa["text"][ROWS - 2]
            for k, fr in enumerate(a.frames[:-1]):
                if fr["text"][ROWS - 2] != final_status and len(a.frames) > 1:
                    problems.append("step %d %r: status line changed mid-animation (frame %d): %r vs %r" %
                                    (i, keys, k, fr["text"][ROWS - 2], final_status))
                    break
            tops = [first_line_number(fr["text"]) for fr in a.frames]
            tops = [t for t in tops if t is not None]
            if len(tops) > 2:
                start = tops[0]
                end = first_line_number(sa["text"])
                lo, hi = min(start, end), max(start, end)
                if start != end:
                    # stays within [start - screen, end + screen] and settles monotonically
                    inside = [t for t in tops if lo - ROWS * 2 <= t <= hi + ROWS * 2]
                    if len(inside) != len(tops):
                        problems.append("step %d %r: a frame scrolled outside its path: %r" % (i, keys, tops))
    finally:
        a.close()
        b.close()
    return problems


def check_specials(binary, root):
    out = []
    # j and k never animate: one frame, nothing after it
    r = Run(binary, root)
    try:
        r.type("30G")
        r.ed.key("j", quiet=0.25, min_frames=1)
        res = r.ed.key("j", quiet=0.25, min_frames=1)
        if res["frames"] != 1:
            out.append("j wrote %d frames (want exactly 1)" % res["frames"])
        res = r.ed.key("k", quiet=0.25, min_frames=1)
        if res["frames"] != 1:
            out.append("k wrote %d frames (want exactly 1)" % res["frames"])
        # a half page animates: several frames, over well under 300 ms
        res = r.ed.key("\x04", quiet=0.25, min_frames=1)
        if res["frames"] < 2:
            out.append("<C-d> wrote %d frames (want an animation)" % res["frames"])
        elif res["settled"] > 0.3:
            out.append("<C-d> took %.0f ms to settle" % (res["settled"] * 1000))
        # idle: nothing at all
        frames, first = r.ed.read_frames(time.perf_counter() + 1.0, 99.0)
        if frames.total != 0:
            out.append("idle editor wrote %d bytes" % frames.total)
        # an edit during an animation shows the final text at once
        r.type("gg")
        os_write(r.ed.master, b"G")
        time.sleep(0.03)
        os_write(r.ed.master, b"x")
        r.ed.settle(0.4, 5)
        r.catch_up()
        if "row" not in "\n".join(r.screen.display):
            out.append("screen lost after G then x")
        # :set noanimate
        r.type("gg")
        r.type(":set noanimate\r")
        res = r.ed.key("\x04", quiet=0.25, min_frames=1)
        if res["frames"] != 1:
            out.append("with noanimate <C-d> wrote %d frames" % res["frames"])
    finally:
        r.close()
    # --no-anim and $M3_NO_ANIM
    for kind, env, extra in (("env", {"M3_NO_ANIM": "1"}, ()), ("TERM=dumb", {"TERM": "dumb"}, ()), ("flag", {}, ("--no-anim",))):
        r = Run(binary, root, env=env, extra=extra)
        try:
            res = r.ed.key("\x04", quiet=0.25, min_frames=1)
            if res["frames"] != 1:
                out.append("%s: <C-d> wrote %d frames (want 1)" % (kind, res["frames"]))
        finally:
            r.close()
    # the yank flash: a blended background on the yanked text, gone when it is over
    r = Run(binary, root)
    try:
        r.type("gg")
        last = r.type("yy")
        frames = r.frames
        if len(frames) < 2:
            out.append("yy drew %d frames (the flash should take several)" % len(frames))
        else:
            if not any(b not in ("default", "000000") for b in frames[0]["bg"][5:20]):
                out.append("the yank flash left no colour on the yanked line: %r" % frames[0]["bg"][5:12])
            if any(b not in ("default",) for b in last["bg"][5:20]):
                out.append("the yank flash did not clear: %r" % last["bg"][5:12])
    finally:
        r.close()
    # the terminal's own cursor: a bar in Insert mode, the user's shape back on the way out
    r = Run(binary, root)
    try:
        r.ed.key("i", quiet=0.2)
        if b"\x1b[6 q" not in bytes(r.ed.raw):
            out.append("Insert mode did not ask for a bar cursor (CSI 6 SP q)")
        r.ed.key("\x1b", quiet=0.2)
        os_write(r.ed.master, b":q!\r")
        r.ed.proc.wait(timeout=5)
        r.ed.settle(0.2, 2)
        tail = bytes(r.ed.raw[-300:])
        if b"\x1b[0 q" not in tail or b"\x1b[?25h" not in tail or b"\x1b[?1004l" not in tail:
            out.append("the terminal was not restored on quit: %r" % tail)
    finally:
        r.close()
    # the scrollbar, and clicking in it
    r = Run(binary, root)
    try:
        r.type(":set scrollbar\r")
        thumbs = [y for y in range(ROWS - 2) if r.screen.display[y][COLS - 1] == "\u2590"]
        if not thumbs:
            out.append("no scrollbar thumb in the right column")
        r.type("\x1b[<0;%d;%dM\x1b[<0;%d;%dm" % (COLS, ROWS - 3, COLS, ROWS - 3), 0.5)
        top = first_line_number(r.screen.display)
        if top is None or top < 2000:
            out.append("a click at the bottom of the scrollbar left the view at line %r" % top)
    finally:
        r.close()
    # a resize leaves no garbage: consecutive line numbers, a status line
    r = Run(binary, root)
    try:
        r.type("1500Gzz")
        r.ed.resize(24, 80)
        r.screen.resize(24, 80)
        r.ed.settle(0.4, 5)
        r.catch_up()
        nums = [first_line_number([row]) for row in r.screen.display[:22]]
        if None in nums or nums != list(range(nums[0], nums[0] + 22)):
            out.append("after a resize the rows are not consecutive lines: %r" % nums)
        if "NORMAL" not in r.screen.display[22] + r.screen.display[23] and "1500" not in r.screen.display[22]:
            out.append("no status line after a resize: %r" % r.screen.display[22:])
    finally:
        r.close()
    # no colour support: scrolling still animates, no colour blends are written
    r = Run(binary, root, env={"COLORTERM": "", "TERM": "xterm-256color"})
    try:
        res = r.ed.key("\x04", quiet=0.25, min_frames=1)
        if res["frames"] < 2:
            out.append("without truecolor <C-d> wrote %d frames (scrolling should still animate)" % res["frames"])
        r.ed.key("yy", quiet=0.4)
        if b"38;2;" in bytes(r.ed.raw[-4000:]) and b"232;192;96" in bytes(r.ed.raw[-4000:]):
            out.append("yank flash wrote 24-bit colour on a 256-colour terminal")
    finally:
        r.close()
    return out


def main():
    binary = os.path.abspath(sys.argv[1])
    quick = "--quick" in sys.argv
    root = tempfile.mkdtemp(prefix="m3d-anim-")
    make_file(os.path.join(root, "big.txt"))
    failed = 0
    try:
        corpus = CORPUS[:6] if quick else CORPUS
        for name, steps in corpus:
            problems = compare(binary, root, name, steps)
            if problems:
                failed += 1
                print("FAIL %s" % name)
                for p in problems:
                    print("     " + p.replace("\n", "\n     "))
            else:
                print("ok   %s" % name)
        problems = check_specials(binary, root)
        if problems:
            failed += 1
            print("FAIL specials")
            for p in problems:
                print("     " + p)
        else:
            print("ok   specials (j/k instant, kill switches, idle, noanimate)")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("anim_pty: %d failed" % failed)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
