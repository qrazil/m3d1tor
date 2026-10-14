# Benchmarks

`bench.py` drives m3, nvim and hx in a real pty (200 x 60 unless
`BENCH_ROWS` / `BENCH_COLS` say otherwise) with the same key stream and
reports, per editor:

* startup on a 1k-line file (spawn to the last byte of the first frame)
* opening a large file and its peak resident memory (`VmHWM`)
* `/needle` and 20 x `n`, 200 x `<C-d>`, 200 x `<C-f>`, 2000 typed characters,
  `:%s` (not for hx)

```
python3 bench/bench.py --m3d ./m3 --lines 100000 --runs 5
```

A step is finished when the editor has been quiet for 150 ms; the 150 ms are
subtracted, so a value of 0.0000 means "faster than the harness can see".
Numbers are only worth what the machine and the run say: the results of a run
belong in the benchmark repository, next to the host description.

Second run (Linux x86-64, 100000 lines, 5 runs; v0.0.2 plus input coalescing):

| measurement | m3 | nvim -u NONE | hx |
|---|---|---|---|
| startup, 1k lines (s) | 0.016 | 0.119 | 0.066 |
| open 100k lines (s) | 0.068 | 0.119 | 0.547 |
| open 100k lines, peak RSS (MB) | 26.8 | 7.9 | 102.9 |
| `/needle_rare` (s) | 0.003 | 0.002 | < 0.001 |
| 20 x `n` (s) | 0.003 | 0.009 | < 0.001 |
| 200 x `<C-d>` (s) | 0.044 | 0.056 | < 0.001 |
| 200 x `<C-f>` (s) | 0.073 | 0.086 | < 0.001 |
| 2000 typed characters (s) | 0.056 | 0.051 | < 0.001 |
| 1 MB bracketed paste (s) | 0.50 | 0.059 | 0.020 |
| `:%s/alpha/omega/g` (s) | < 0.001 | 0.092 | n/a |
| peak RSS after the steps (MB) | 48.2 | 7.8 | 100.4 |

The first run, before input coalescing, was 4.5 s for 2000 typed characters
(one frame per key event, about 1.5 ms each at 200 x 60) and 0.68 s for 200 x
`<C-d>`. The loop now handles every event that has already arrived (up to 512)
before it draws, so a burst of typing, a macro or a paste costs one frame.
A bracketed paste is one edit: it is typed without autoindent, auto-pairs or
mappings, and one `u` takes it back. hx did not understand some of the key
streams (its numbers are the time to nothing); read them as "no result".
