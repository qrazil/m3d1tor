#!/usr/bin/env python3
"""End-to-end checks of the real m3d1tor binary in a pty.

    python3 tests/e2e.py ./m3d1tor [--only NAME]

The screen is rebuilt with pyte (skipped with a note when pyte is missing).
Each scenario starts a fresh editor in a temporary project directory, types
keys and waits for text on the screen.
"""
import fcntl
import os
import pty
import select
import shutil
import struct
import subprocess
import sys
import tempfile
import termios
import time

try:
    import pyte
except ImportError:
    print("skip e2e: pyte is not installed")
    sys.exit(0)

ROWS, COLS = 30, 100


class Session:
    def __init__(self, binary, cwd, args=(), rows=ROWS, cols=COLS, env=None):
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        full = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor", LANG="C.UTF-8",
                    HOME=cwd, XDG_CONFIG_HOME=os.path.join(cwd, ".config"),
                    XDG_STATE_HOME=os.path.join(cwd, ".state"))
        full.pop("M3D1TOR_KEYMAP", None)
        if env:
            full.update(env)
        self.proc = subprocess.Popen([binary, "-u", "NONE"] + list(args), stdin=slave, stdout=slave,
                                     stderr=slave, cwd=cwd, env=full, start_new_session=True,
                                     close_fds=True)
        os.close(slave)
        self.master = master
        self.screen = pyte.Screen(cols, rows)
        self.stream = pyte.ByteStream(self.screen)

    def pump(self, seconds=0.2):
        end = time.time() + seconds
        while time.time() < end:
            ready, _, _ = select.select([self.master], [], [], 0.05)
            if ready:
                try:
                    data = os.read(self.master, 65536)
                except OSError:
                    return
                if not data:
                    return
                self.stream.feed(data)

    def text(self):
        return "\n".join(self.screen.display)

    def send(self, keys, settle=0.15):
        if isinstance(keys, str):
            keys = keys.encode()
        os.write(self.master, keys)
        self.pump(settle)

    def wait_for(self, needle, timeout=5.0):
        end = time.time() + timeout
        while time.time() < end:
            self.pump(0.1)
            if needle in self.text():
                return True
        return False

    def close(self):
        try:
            os.write(self.master, b"\x1b\x1b:qa!\r")
        except OSError:
            pass
        end = time.time() + 3
        while time.time() < end and self.proc.poll() is None:
            self.pump(0.05)
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait()
        os.close(self.master)


SCENARIOS = {}


def scenario(fn):
    SCENARIOS[fn.__name__] = fn
    return fn


def project():
    root = tempfile.mkdtemp(prefix="m3d-e2e-")
    with open(os.path.join(root, "hello.txt"), "w") as f:
        f.write("hello world\nsecond line\nthird needle line\n")
    os.makedirs(os.path.join(root, "src"))
    with open(os.path.join(root, "src", "main.py"), "w") as f:
        f.write("def main():\n    return 42  # TODO later\n")
    return root


@scenario
def leader_which_key(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world"), s.text()
        s.send(" ", settle=0.8)
        assert s.wait_for("find"), "leader which-key missing:\n" + s.text()
        assert "Write file" in s.text(), s.text()
    finally:
        s.close()


@scenario
def prefix_which_key(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send("g", settle=0.8)
        assert s.wait_for("first line"), "g which-key missing:\n" + s.text()
        s.send("\x1b")
        s.send("\x17", settle=0.8)
        assert s.wait_for("split below"), "ctrl-w which-key missing:\n" + s.text()
        s.send("\x1b")
        s.send("d", settle=0.8)
        assert s.wait_for("paragraph"), "operator which-key missing:\n" + s.text()
    finally:
        s.close()


@scenario
def jk_escape(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send("ixx")
        s.send("jk", settle=0.2)
        assert s.wait_for("NORMAL") or "INSERT" not in s.text(), s.text()
        s.send(":set nojk_escape\r")
        s.send("ijk")
        assert "jk" in s.text().split("\n")[0], s.text()
    finally:
        s.close()


@scenario
def plugins_command(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send(":Plugins\r")
        assert s.wait_for("finder"), s.text()
        s.send("\x1b")
        s.send(":PluginDisable finder\r")
        s.send(" f", settle=0.8)
        assert "Find files" not in s.text(), "finder rows should be gone:\n" + s.text()
    finally:
        s.close()


def main():
    binary = os.path.abspath(sys.argv[1])
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    failed = 0
    for name, fn in SCENARIOS.items():
        if only and name != only:
            continue
        root = project()
        try:
            fn(binary, root)
            print("ok   %s" % name)
        except AssertionError as error:
            failed += 1
            print("FAIL %s: %s" % (name, error))
        except Exception as error:  # noqa
            failed += 1
            print("FAIL %s: %r" % (name, error))
        finally:
            shutil.rmtree(root, ignore_errors=True)
    print("e2e: %d scenarios, %d failed" % (len(SCENARIOS) if not only else 1, failed))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
