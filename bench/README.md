# Benchmarks

`bench.py` drives m3d1tor, nvim and hx in a real pty (200 x 60 unless
`BENCH_ROWS` / `BENCH_COLS` say otherwise) with the same key stream and
reports, per editor:

* startup on a 1k-line file (spawn to the last byte of the first frame)
* opening a large file and its peak resident memory (`VmHWM`)
* `/needle` and 20 x `n`, 200 x `<C-d>`, 200 x `<C-f>`, 2000 typed characters,
  `:%s` (not for hx)

```
python3 bench/bench.py --m3d ./m3d1tor --lines 100000 --runs 5
```

A step is finished when the editor has been quiet for 150 ms; the 150 ms are
subtracted, so a value of 0.0000 means "faster than the harness can see".
Numbers are only worth what the machine and the run say: the results of a run
belong in the benchmark repository, next to the host description.

First run (Linux x86-64, 100000 lines, 5 runs):

| measurement | m3d1tor | nvim -u NONE | hx |
|---|---|---|---|
| startup, 1k lines (s) | 0.025 | 0.129 | 0.084 |
| open 100k lines (s) | 0.089 | 0.126 | 0.560 |
| open 100k lines, peak RSS (MB) | 26.8 | 7.7 | 91.6 |
| `/needle_rare` (s) | 0.030 | 0.004 | < 0.001 |
| 20 x `n` (s) | 0.062 | 0.023 | < 0.001 |
| 200 x `<C-d>` (s) | 0.68 | 0.083 | < 0.001 |
| 200 x `<C-f>` (s) | 0.66 | 0.107 | < 0.001 |
| 2000 typed characters (s) | 4.5 | 0.051 | 0.003 |
| `:%s/alpha/omega/g` (s) | 0.038 | 0.111 | n/a |

m3d1tor renders after every key event it is handed, so a burst of 2000 keys
costs 2000 frames (about 1.5 ms each at 200 x 60); nvim and hx coalesce. A
single typed key or a bracketed paste is not affected.
