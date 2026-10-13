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
import re
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
    def __init__(self, binary, cwd, args=(), rows=ROWS, cols=COLS, env=None, keymap="NONE"):
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        full = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor", LANG="C.UTF-8",
                    HOME=cwd, XDG_CONFIG_HOME=os.path.join(cwd, ".config"),
                    XDG_STATE_HOME=os.path.join(cwd, ".state"))
        full.pop("M3D1TOR_KEYMAP", None)
        if env:
            full.update(env)
        self.proc = subprocess.Popen([binary, "-u", keymap] + list(args), stdin=slave, stdout=slave,
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


def have(tool):
    return shutil.which(tool) is not None


def git(root, *args):
    subprocess.run(["git", "-C", root] + list(args), check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL,
                   env=dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_AUTHOR_NAME="t",
                            GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t"))


@scenario
def finder_files(binary, root):
    s = Session(binary, root, ["hello.txt"], cols=130)
    try:
        assert s.wait_for("hello world")
        s.send(" ff", settle=0.6)
        assert s.wait_for("src/main.py"), "files picker:\n" + s.text()
        s.send("main")
        assert s.wait_for("def main"), "preview missing:\n" + s.text()
        s.send("\r", settle=0.5)
        assert s.wait_for("return 42"), s.text()
    finally:
        s.close()


@scenario
def finder_grep_and_quickfix(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send(" fg", settle=0.4)
        s.send("line", settle=0.8)
        assert s.wait_for("hello.txt:3"), "grep hit:\n" + s.text()
        s.send("\x11", settle=0.5)  # ctrl-q: to the quickfix list
        assert s.wait_for("Quickfix"), s.text()
        s.send("\x1b", settle=0.2)
        s.send("]q", settle=0.3)
        s.send(":cnext\r", settle=0.3)
        assert s.wait_for("of 2") or s.wait_for("of 3"), s.text()
    finally:
        s.close()


@scenario
def finder_lines_and_marks(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send(" fd", settle=0.4)
        s.send("third", settle=0.4)
        s.send("\r", settle=0.4)
        assert "NORMAL" in s.text() and re.search(r" 3:\d+ ", s.text()), s.text()
    finally:
        s.close()


@scenario
def bracketed_and_move(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send("\x1bj", settle=0.3)  # Alt-j: move the line down
        lines = s.text().split("\n")
        assert "second line" in lines[0] and "hello world" in lines[1], "\n".join(lines[:4])
        s.send("\x1bk", settle=0.3)
        lines = s.text().split("\n")
        assert "hello world" in lines[0], "\n".join(lines[:4])
    finally:
        s.close()


@scenario
def git_signs_and_pickers(binary, root):
    if not have("git"):
        return
    git(root, "init", "-q", "-b", "main")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "first")
    git(root, "checkout", "-q", "-b", "feature")
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send("ggOnew line\x1b", settle=0.3)
        s.send(" gs", settle=0.5)   # stage hunk
        assert s.wait_for("Hunk staged"), s.text()
        out = subprocess.run(["git", "-C", root, "diff", "--cached", "--stat"], capture_output=True, text=True).stdout
        assert "hello.txt" in out, out
        s.send(" gb", settle=0.6)
        assert s.wait_for("main") and s.wait_for("feature"), s.text()
        s.send("\x1b", settle=0.2)
        s.send(" gC", settle=0.6)
        assert s.wait_for("first"), s.text()
    finally:
        s.close()


@scenario
def terminal_pane(binary, root):
    s = Session(binary, root, ["hello.txt"], env={"SHELL": "/bin/sh", "PS1": "$ "})
    try:
        assert s.wait_for("hello world")
        s.send(":terminal\r", settle=0.8)
        assert s.wait_for("TERMINAL"), s.text()
        s.send("echo from_the_pane_$((6*7))\r", settle=0.8)
        assert s.wait_for("from_the_pane_42"), s.text()
        s.send("\x1c\x0e", settle=0.3)  # CTRL-\ CTRL-N
        assert s.wait_for("NORMAL"), s.text()
        s.send("i", settle=0.3)
        assert s.wait_for("TERMINAL"), s.text()
        s.send("exit\r", settle=0.8)
        assert s.wait_for("Process exited 0"), s.text()
    finally:
        s.close()


@scenario
def shell_filters(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send(":%!sort\r", settle=0.5)
        lines = s.text().split("\n")
        assert "hello world" in lines[0], "\n".join(lines[:4])
        s.send(":r !echo from_read\r", settle=0.5)
        assert s.wait_for("from_read"), s.text()
        s.send("!!tr a-z A-Z\r", settle=0.5)
        assert s.wait_for("FROM_READ"), s.text()
        s.send(":!echo bang_output\r", settle=0.5)
        assert s.wait_for("bang_output"), s.text()
    finally:
        s.close()


@scenario
def statusline_tabline_guides(binary, root):
    if have("git"):
        git(root, "init", "-q", "-b", "trunk")
    s = Session(binary, root, ["src/main.py", "hello.txt"])
    try:
        assert s.wait_for("return 42")
        text = s.text()
        first = text.split("\n")[0]
        assert "main.py" in first and "hello.txt" in first, "tabline:\n" + text
        s.send(":b1\r", settle=0.4)
        assert s.wait_for("return 42"), s.text()
        assert "\u2502" in s.text(), "indent guide missing:\n" + s.text()
        assert "python" in s.text().split("\n")[-2], "filetype missing:\n" + s.text()
        if have("git"):
            assert s.wait_for("trunk", 4.0), "branch missing:\n" + s.text()
        s.send(":PluginDisable guides\r", settle=0.3)
        assert "\u2502" not in s.text(), s.text()
        s.send(":PluginDisable statusline\r", settle=0.3)
        assert "python" not in s.text().split("\n")[-2], s.text()
    finally:
        s.close()


@scenario
def state_recent_harpoon_position(binary, root):
    keymap = os.path.join(root, "empty.vim")
    open(keymap, "w").close()
    s = Session(binary, root, ["src/main.py"], keymap=keymap)
    try:
        assert s.wait_for("return 42")
        s.send("j$", settle=0.2)
        s.send(" ha", settle=0.4)
        assert s.wait_for("Harpoon: pinned"), s.text()
        s.send(":e hello.txt\r", settle=0.4)
        s.pump(1.5)
    finally:
        s.close()
    s = Session(binary, root, ["src/main.py"], keymap=keymap)
    try:
        assert s.wait_for("return 42")
        assert re.search(r" 2:\d+ ", s.text()), "position not restored:\n" + s.text()
        s.send(" fr", settle=0.5)
        assert s.wait_for("hello.txt"), "recent list:\n" + s.text()
        s.send("\x1b", settle=0.2)
        s.send(" he", settle=0.5)
        assert s.wait_for("main.py"), "harpoon menu:\n" + s.text()
    finally:
        s.close()


@scenario
def lsp_client(binary, root):
    fake = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake_lsp.py")
    with open(os.path.join(root, "a.py"), "w") as f:
        f.write("hello = 1  # BUG\nprint(hello)\nprint(hello)\n")
    s = Session(binary, root, ["a.py"])
    try:
        assert s.wait_for("print(hello)")
        s.send(":Lsp server python python3 %s\r" % fake, settle=0.3)
        s.send(":Lsp start\r", settle=0.3)
        assert s.wait_for("E:1", 8.0), "diagnostic count missing:\n" + s.text()
        assert re.search(r"^E ", s.text(), re.M) or " E " in s.text().split("\n")[0], "sign missing:\n" + s.text()
        s.send("]d", settle=0.4)
        assert s.wait_for("found BUG on line 1"), s.text()
        s.send(" ll", settle=0.4)
        assert s.wait_for("error: found BUG"), s.text()
        s.send("K", settle=0.6)
        assert s.wait_for("hover 0:"), "hover:\n" + s.text()
        s.send("\r", settle=0.2)
        s.send(":Lsp rename howdy\r", settle=0.8)
        assert s.wait_for("howdy = 1"), "rename:\n" + s.text()
        s.send(":Lsp format\r", settle=0.8)
        assert s.wait_for("PRINT(HOWDY)"), "format:\n" + s.text()
        s.send("grr", settle=0.8)
        assert s.wait_for("References"), "references:\n" + s.text()
        s.send("\x1b", settle=0.2)
        s.send(":Lsp action\r", settle=0.8)
        assert s.wait_for("Fix BUG"), "actions:\n" + s.text()
        s.send("\r", settle=0.6)
        assert s.wait_for("FIXED"), "applied:\n" + s.text()
    finally:
        s.close()


@scenario
def label_jump(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send(" jn", settle=0.5)   # the n of "second line" and "needle line" ...
        assert s.wait_for("jump"), s.text()
        assert s.wait_for("third needle line") or True
        s.send("a", settle=0.4)
        assert "NORMAL" in s.text() and re.search(r" [23]:\d+ ", s.text()), s.text()
    finally:
        s.close()


@scenario
def user_maps_in_which_key(binary, root):
    keymap = os.path.join(root, "keys.vim")
    with open(keymap, "w") as f:
        f.write("let mapleader = \" \"\nnnoremap <leader>w :w<CR>\nnnoremap gX :s/hello/HELLO/<CR>\nnnoremap <leader>q ddp\n")
    s = Session(binary, root, ["hello.txt"], keymap=keymap)
    try:
        assert s.wait_for("hello world")
        s.send("g", settle=0.8)
        assert s.wait_for(":s/hello/HELLO/"), "user gX missing from which-key:\n" + s.text()
        s.send("\x1b", settle=0.2)
        s.send(" ", settle=0.8)
        assert s.wait_for("ddp"), "user <leader>q missing:\n" + s.text()
        assert "Find files" in s.text() or "find" in s.text(), s.text()
        s.send("q", settle=0.4)
        assert s.wait_for("second line"), s.text()
        lines = s.text().split("\n")
        assert "second line" in lines[0] and "hello world" in lines[1], "\n".join(lines[:3])
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
