#!/usr/bin/env python3
"""Benchmarks of m3d1tor against nvim and hx (DESIGN.md section 8).

Each editor runs in a real pty (200 x 60) with a scripted key stream. A step is
finished when the editor has been quiet for QUIET seconds after the keys, which
is the same rule for all three. Peak memory is VmHWM from /proc.

    python3 bench/bench.py --m3d ./m3d1tor [--nvim nvim] [--hx hx] [--lines 100000]
                           [--runs 10] [--only startup,open,search,...]

Fixtures are generated deterministically into a temporary directory. The
numbers are printed as a table; nothing is claimed without running this.
"""
import argparse
import fcntl
import os
import pty
import random
import select
import shutil
import statistics
import struct
import subprocess
import sys
import tempfile
import termios
import time

QUIET = 0.15
ROWS, COLS = int(os.environ.get("BENCH_ROWS", "60")), int(os.environ.get("BENCH_COLS", "200"))


def make_source(path, lines, seed=1):
    rng = random.Random(seed)
    words = ["alpha", "beta", "gamma", "delta", "value", "index", "count", "result", "buffer", "needle_rare"]
    with open(path, "w") as f:
        for i in range(lines):
            indent = "    " * rng.randrange(0, 4)
            a, b, c = (rng.choice(words) for _ in range(3))
            if i % 9973 == 7:
                f.write("%sunique_marker_%d = %s\n" % (indent, i, "needle_rare"))
            else:
                f.write("%sint %s_%d = %s(%s, %d); // %s\n" % (indent, a, i, b, c, rng.randrange(1000), "line"))


def spawn(argv, cwd):
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))
    env = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor", LANG="C.UTF-8")
    proc = subprocess.Popen(argv, stdin=slave, stdout=slave, stderr=slave, cwd=cwd, env=env,
                            start_new_session=True, close_fds=True)
    os.close(slave)
    return proc, master


def drain(master, quiet=QUIET, limit=120.0, first_byte=False):
    """Read until no output for `quiet` seconds; returns (seconds until the last byte, bytes)."""
    start = time.time()
    last = start
    got = 0
    while True:
        remaining = limit - (time.time() - start)
        if remaining <= 0:
            break
        ready, _, _ = select.select([master], [], [], min(quiet, remaining))
        if ready:
            try:
                chunk = os.read(master, 65536)
            except OSError:
                break
            if not chunk:
                break
            got += len(chunk)
            last = time.time()
        elif got > 0 or not first_byte:
            if time.time() - last >= quiet:
                break
    return last - start, got


def hwm_kb(pid):
    try:
        with open("/proc/%d/status" % pid) as f:
            for line in f:
                if line.startswith("VmHWM"):
                    return int(line.split()[1])
    except OSError:
        pass
    return 0


def stop(proc, master):
    try:
        os.write(master, b"\x1b\x1b:qa!\r")
        time.sleep(0.05)
    except OSError:
        pass
    try:
        proc.kill()
    except OSError:
        pass
    proc.wait()
    os.close(master)


def editor_argv(name, binary, path):
    if name == "nvim":
        return [binary, "-u", "NONE", "-n", "-i", "NONE", path]
    if name == "hx":
        return [binary, path]
    return [binary, "-u", "NONE", path]


def session(name, binary, path, steps, cwd):
    """Open `path`, then run each (label, keys) step; returns {label: seconds}, peak kB."""
    proc, master = spawn(editor_argv(name, binary, path), cwd)
    result = {}
    t0 = time.time()
    open_seconds, _ = drain(master, first_byte=True)
    result["open"] = open_seconds
    for label, keys in steps:
        began = time.time()
        os.write(master, keys)
        quiet_seconds, _ = drain(master)
        result[label] = time.time() - began - QUIET
    peak = hwm_kb(proc.pid)
    stop(proc, master)
    return result, peak


def median(values):
    return statistics.median(values) if values else float("nan")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--m3d", default="./m3d1tor")
    parser.add_argument("--nvim", default="nvim")
    parser.add_argument("--hx", default="hx")
    parser.add_argument("--lines", type=int, default=100000)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    editors = [("m3d1tor", args.m3d), ("nvim", args.nvim), ("hx", args.hx)]
    editors = [(n, b) for n, b in editors if shutil.which(b) or os.path.exists(b)]
    only = set(filter(None, args.only.split(",")))
    work = tempfile.mkdtemp(prefix="m3d-bench-")
    small = os.path.join(work, "small.c")
    big = os.path.join(work, "big.c")
    make_source(small, 1000)
    make_source(big, args.lines)
    rows = []

    def want(name):
        return not only or name in only

    # startup: spawn to the first quiet frame, on the small file
    if want("startup"):
        for name, binary in editors:
            times = []
            for _ in range(args.runs):
                proc, master = spawn(editor_argv(name, binary, small), work)
                seconds, _ = drain(master, first_byte=True)
                times.append(seconds)
                stop(proc, master)
            rows.append(("startup 1k lines (s, median)", name, median(times)))
    # open the big file and measure peak memory
    if want("open"):
        for name, binary in editors:
            times, peaks = [], []
            for _ in range(max(1, args.runs // 2)):
                result, peak = session(name, binary, big, [], work)
                times.append(result["open"])
                peaks.append(peak)
            rows.append(("open %d lines (s, median)" % args.lines, name, median(times)))
            rows.append(("open %d lines peak RSS (MB)" % args.lines, name, median(peaks) / 1024.0))
    # search, replace, scroll, typing on the big file
    if want("search") or want("scroll") or want("typing") or want("replace"):
        for name, binary in editors:
            steps = []
            if want("search"):
                steps.append(("search rare", b"/needle_rare\r"))
                steps.append(("search n x20", b"n" * 20))
            if want("scroll"):
                steps.append(("scroll <C-d> x200", (b"\x04" if name != "hx" else b"\x04") * 200))
                steps.append(("page down x200", b"\x06" * 200 if name != "hx" else b"\x06" * 200))
            if want("typing"):
                steps.append(("type 2000 chars", b"i" + b"x" * 2000 + b"\x1b" if name != "hx" else b"i" + b"x" * 2000 + b"\x1b"))
            if want("replace") and name != "hx":
                steps.append(("replace-all :%s", b":%s/alpha/omega/g\r"))
            result, peak = session(name, binary, big, steps, work)
            for label, _ in steps:
                rows.append((label + " (s)", name, result.get(label, float("nan"))))
            rows.append(("peak RSS after steps (MB)", name, peak / 1024.0))
    shutil.rmtree(work, ignore_errors=True)
    labels = []
    for label, _, _ in rows:
        if label not in labels:
            labels.append(label)
    names = [n for n, _ in editors]
    print("%-38s" % "measurement" + "".join("%12s" % n for n in names))
    for label in labels:
        line = "%-38s" % label
        for name in names:
            value = [v for (l, n, v) in rows if l == label and n == name]
            line += "%12.4f" % value[0] if value else "%12s" % "-"
        print(line)


if __name__ == "__main__":
    sys.exit(main())
