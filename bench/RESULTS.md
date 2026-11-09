# Kestrel mate-speed results

Date: 2026-11-09

All games use Maia-3 5M on CPU at 1500 Elo, temperature 1.0, the standard start
position, a 180-ply cap, and the 12 fixed seeds below. Lower moves-to-mate is
better. A win means Kestrel mated Maia.

## Deterministic protocol

The time-limited protocol was not reproducible. The deterministic protocol is:

- Kestrel 0.1.0 AVX2 (`bin/windows-x86_64/kestrel-0.1.0-avx2.exe`)
- **Threads 1**, Hash 1024 MB
- Fixed search depth: **root 18**, **leaf 15**, **deep root 18**
- MultiPV 4; deep MultiPV 1
- No wall-clock search limit during play
- Same Maia seed, board, and temperature for every arm

Command:

```bash
.cache/src/vala/.venv/Scripts/python.exe \
  kestrel/bench/mate_vs_vala.py \
  --games 12 --arms kestrel \
  --kestrel-root-depth 18 --kestrel-leaf-depth 15 \
  --kestrel-deep-root-depth 18 \
  --kestrel-multipv 4 --kestrel-deep --kestrel-deep-multipv 1 \
  --kestrel-threads 1 \
  --out out/kestrel-det-12
```

The 12-game run took 843.55 seconds of game wall time for 235 White moves,
about **3.59 s per White move**. The old wall-clock-limited run averaged about
3.86 s per White move, so the fixed-depth protocol is not slower per move.

## Deterministic baseline

Two complete 12-seed runs produced **identical move counts**, all 12 wins:

| Seed | Run 1 | Run 2 |
|---:|---:|---:|
| 101003 | 12 | 12 |
| 201006 | 25 | 25 |
| 301009 | 19 | 19 |
| 401012 | 28 | 28 |
| 501015 | 23 | 23 |
| 601018 | 27 | 27 |
| 701021 | 17 | 17 |
| 801024 | 19 | 19 |
| 901027 | 17 | 17 |
| 1001030 | 7 | 7 |
| 1101033 | 23 | 23 |
| 1201036 | 18 | 18 |

- **Mean: 19.58 moves to mate**
- **Wins: 12/12 in both runs**
- **Repeat: bit-identical per-seed move counts**
- **Does this beat 18.58? No.** The old 18.58 was a single wall-clock-limited
  sample and is not comparable to the deterministic protocol.

## Zero-search re-ranking screen (not adopted)

The variant reused the existing top-1 deep search results and the Maia reply
probability already returned by `predict`, with no additional engine search.
It traded up to 0.75 of a nominal mate-distance step for a more likely modeled
reply.

- Seed 101003: **loss**, 30 White moves, 60 plies.
- The two-seed screen was stopped immediately; seed 201006 was not run.
- The re-rank path was removed, and the deterministic baseline above was
  reproduced exactly.

## Legacy wall-clock result (18.58; not deterministic)

This is the earlier time-limited run, retained for history only. It used root
500 ms, leaf 300 ms, deep root 500 ms, MultiPV 4, deep MultiPV 1, and 8 threads.
A two-seed recheck produced different counts (23 and 15 instead of 17 and 23),
so the 18.58 figure is not a trustworthy A/B baseline.

| Seed | Moves |
|---:|---:|
| 101003 | 17 |
| 201006 | 23 |
| 301009 | 19 |
| 401012 | 26 |
| 501015 | 24 |
| 601018 | 13 |
| 701021 | 18 |
| 801024 | 12 |
| 901027 | 14 |
| 1001030 | 7 |
| 1101033 | 23 |
| 1201036 | 27 |

Mean: **18.58**; all 12 games won.

## Other rejected variants

- Expectimax over Maia's top-2 replies: 16 then 24 moves on the first two
  legacy seeds; roughly twice as slow and not better.
- `DeepMultiPV=2`: 30 moves on legacy seed 101003.
- Doubled root/leaf time: 22 moves on legacy seed 101003.
- Precomputed FEN-keyed high-depth mate book: 31 moves on legacy seed 101003;
  stopped at the two-seed screen.
