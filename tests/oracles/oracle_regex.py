#!/usr/bin/env python3
"""Differential oracle for the Vim regex engine (MED_regex) against nvim.

    python3 tests/oracles/oracle_regex.py --runner BIN [--corpus] [--fuzz]
                                          [--seed N] [--cases N] [-v]

BIN is tests/t_regex_run.m31 built. Corpus lines (tests/oracles/regex_cases.txt)
are `PATTERN<TAB>TEXT<TAB>FLAGS`, raw (no escaping; `<TAB>` stands for a tab in
either field; FLAGS may hold `i` = ignorecase, `s` = smartcase). Both sides
print leftmost-match byte offsets and the nine groups; the nvim side is
`matchstrpos()` / `matchlist()` on the text. Fuzz cases build random patterns
from a fragment table over a small alphabet, from a seed.
"""
import argparse
import binascii
import os
import random
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
NVIM = os.environ.get("NVIM", "nvim")
LUA = os.path.join(HERE, "nvim_regex.lua")
CORPUS = os.path.join(HERE, "regex_cases.txt")
KNOWN = os.path.join(HERE, "known_regex_divergences.txt")


def hexs(s):
    return binascii.hexlify(s.encode("utf-8")).decode("ascii")


def unplace(s):
    return s.replace("<TAB>", "\t")


def load(path):
    cases = []
    if not os.path.exists(path):
        return cases
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            flags = parts[2] if len(parts) > 2 else ""
            cases.append((parts[0], parts[1], flags))
    return cases


FRAGMENTS = [
    "a", "b", "ab", "A", "1", "_", " ", ".", "\\.", "[ab]", "[^a]", "[a-c]", "[[:alpha:]]",
    "\\d", "\\w", "\\s", "\\a", "\\u", "\\l", "\\S", "\\W", "\\D", "\\h",
    "^", "$", "\\<", "\\>", "\\zs", "\\ze", "\\(", "\\)", "\\%(", "\\|", "\\&",
    "*", "\\+", "\\=", "\\?", "\\{2}", "\\{1,2}", "\\{-1,}", "\\{-}", "\\{,2}",
    "\\1", "\\@=", "\\@!", "\\@<=", "\\@<!", "\\@>", "\\c", "\\C", "\\v", "\\m", "\\M", "\\V",
    "\\%[ab]", "\\%d97", "\\%x61", "\\%u00e9", "\\%^", "\\%$", "\\%2c", "\\%>1c", "\\%<3c",
    "\\_s", "\\_.", "\\_[a-z]", "\\n", "\\t", "\\e", "é", "日", "(", ")", "|", "+", "?", "=", "{", "@", "<", ">",
]
ALPHABET = ["a", "b", "c", "A", "B", "1", "2", "_", " ", ".", "-", "é", "日", "\t", "aa", "ab"]


def fuzz_case(rng):
    n = rng.randint(1, 6)
    pat = "".join(rng.choice(FRAGMENTS) for _ in range(n))
    text = "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 9)))
    flags = rng.choice(["", "", "", "i", "is"])
    return (pat, text, flags)


def run_nvim(cases, tmp):
    src = os.path.join(tmp, "nv_cases.txt")
    out = os.path.join(tmp, "nv_out.txt")
    with open(src, "w") as f:
        for i, (p, t, fl) in enumerate(cases):
            f.write("%d\t%s\t%s\t%s\n" % (i, hexs(unplace(p)), hexs(unplace(t)), fl))
    subprocess.run([NVIM, "--headless", "-u", "NONE", "-i", "NONE", "-n", "-l", LUA, src, out],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, timeout=120)
    return src, parse(out)


def parse(path):
    res = {}
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if line:
                res[int(line.split("\t")[0])] = line.split("\t")[1:]
    return res


def run_engine(runner, src, tmp):
    done = subprocess.run([runner, src], capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL)
    res = {}
    for line in done.stdout.split("\n"):
        if line:
            res[int(line.split("\t")[0])] = line.split("\t")[1:]
    return res


def compare(cases, runner, verbose):
    with tempfile.TemporaryDirectory(prefix="medre-") as tmp:
        src, nv = run_nvim(cases, tmp)
        en = run_engine(runner, src, tmp)
    bad = []
    for i, case in enumerate(cases):
        a, b = nv.get(i), en.get(i)
        if a != b:
            bad.append((case, a, b))
    return bad


def show(bad, limit):
    for (case, a, b) in bad[:limit]:
        pat, text, flags = case
        print("DIFF pat=%r text=%r flags=%r" % (pat, text, flags))
        print("   nvim:   %s" % (a[:3] if a else a))
        print("   engine: %s" % (b[:3] if b else b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runner", required=True)
    ap.add_argument("--corpus", action="store_true")
    ap.add_argument("--fuzz", action="store_true")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--cases", type=int, default=2000)
    ap.add_argument("--max-report", type=int, default=15)
    ap.add_argument("-v", action="store_true")
    args = ap.parse_args()
    if not args.corpus and not args.fuzz:
        args.corpus = True
    failed = 0
    if args.corpus:
        cases = load(CORPUS)
        known = set(tuple(c) for c in load(KNOWN))
        bad = compare(cases, args.runner, args.v)
        real = [b for b in bad if tuple(b[0]) not in known]
        print("regex corpus: %d cases, %d matched, %d known divergences, %d failed" % (
            len(cases), len(cases) - len(bad), len(bad) - len(real), len(real)))
        show(real, args.max_report)
        failed += len(real)
    if args.fuzz:
        rng = random.Random(args.seed)
        cases = [fuzz_case(rng) for _ in range(args.cases)]
        bad = compare(cases, args.runner, args.v)
        print("regex fuzz seed %d: %d cases, %d failed" % (args.seed, len(cases), len(bad)))
        show(bad, args.max_report)
        failed += len(bad)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
