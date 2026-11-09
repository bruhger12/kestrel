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
- Root forced-mate shortcut: 25 moves on deterministic seed 101003 versus 12;
  stopped at the two-seed screen.
- Root/deep depth 19: 19 moves on deterministic seed 101003 versus 12;
  stopped at the two-seed screen.
- Root/deep depth 17: 17 moves on seed 101003 and 32 on seed 201006,
  versus 12/25; stopped.
- Leaf depth 16: 21 moves on deterministic seed 101003 versus 12; stopped.
- Fastest-game FEN opening book: 25 moves on deterministic seed 101003 versus
  12; stopped at the two-seed screen.

None of these variants was promoted to a full-12 run. The deterministic
baseline above remains the accepted configuration.

## Eval-weight screen (not adopted)

The engine was rebuilt from the same source with GCC 16.2 and a runtime
`EvalScale` multiplier for the NNUE evaluation only (`100` is exact identity).
Depth, MultiPV, threads, and the selector were unchanged. The compiler-matched
control reproduced the first six baseline games exactly. Because the engine
keeps hash state across games, the screen used the normal games 1-6 sequence and
read the required seeds 101003/401012/601018 from it; the control selected total
was **12/28/27 = 67** at **3.13 s/move**.

| EvalScale | Seeds 1/4/6 | Selected total | Selected s/move | Games 1-6 total | Games 1-6 s/move |
|---:|---:|---:|---:|---:|---:|
| 100 control | 12/28/27 | 67 | 3.13 | 134 | 3.13 |
| 80 | 17/22/12 | 51 | 3.17 | 122 | 2.99 |
| 120 | 14/13/19 | 46 | 3.23 | 123 | 3.39 |

The session explored scales 80 and 120 beyond the selected-subset cost gate;
both raised selected-subset seconds/move. Neither survived a full-12 run:

| EvalScale | Full-12 per-seed moves | Mean | Wins | Seconds/move |
|---:|---|---:|---:|---:|
| 80 | 17/36/18/22/17/12/18/20/10/21/14/32 | 19.75 | 12/12 | 3.79 |
| 120 | 14/18/28/13/31/19/15/15/18/23/48/23 | 22.08 | 12/12 | 3.28 |

EvalScale 80 missed both the move gate (19.75) and the cost gate (3.79);
EvalScale 120 missed the move gate despite passing the cost gate. No repeat
full-12 run was made because neither first run met the promotion conditions. The
zero-search slow-seed log tiebreak was not attempted because the eval-weight
lever did not earn a place. The `EvalScale` code and all related wiring were
reverted; the accepted configuration above remains root 18 / leaf 15 / deep root
18 with one thread and mean 19.58.

## Leaf-depth 14 screen (not adopted)

The accepted search shape was probed one leaf ply shallower: root 18, **leaf
14**, deep root 18, MultiPV 4/1, Threads 1. The normal games 1-6 sequence was
used so hash state matched the control. All games were wins, but the selected
seeds did not improve:

| Variant | Seeds 1/4/6 | Selected total | Selected s/move | Games 1-6 total | Games 1-6 s/move |
|---|---:|---:|---:|---:|---:|
| Control | 12/28/27 | 67 | 3.13 | 134 | 3.13 |
| Leaf 14 | 18/35/14 | 67 | 3.57 | 151 | 3.31 |

Leaf 14 tied the control total rather than strictly lowering it, and the
six-game total regressed from 134 to 151. It was not promoted to a full 12.
## MultiPV 6 screen (abandoned on cost)

MultiPV 6 was tested with root 18 / leaf 15 / deep root 18, deep MultiPV 1, and
one thread, using the absolute engine path. The hard cost gate was checked
after seed 101003.

| Variant | Seed 101003 | Seconds | Seconds/move | Control seed | Control s/move |
|---|---:|---:|---:|---:|---:|
| MultiPV 6 | 23 | 127.44 | 5.54 | 12 | 2.67 |

Seed 101003 won but took 23 moves versus 12 for the control and cost 5.54
s/move, above the 3.59 baseline ceiling. The screen was abandoned immediately;
games 2-6 and any full-12 promotion were not run.

The adjacent root depths 17 and 19 were not re-screened because both are already
recorded negatives. The zero-search log tiebreak was not attempted because no
candidate-level slow-seed log exists, and the previously measured policy-based
tiebreak remains a rejected lever.

## Deep one-ply fallback ablation (aborted, not adopted)

This screen removed the deep mode's one-ply leaf rank, leaving only the two-ply
line rank. The configuration was otherwise unchanged: root 18 / leaf 15 / deep
root 18, MultiPV 4/1, Threads 1. The normal games 1-6 sequence was used.

| Variant | Seeds 1/2 | First-two total | Games 1-2 s/move |
|---|---:|---:|---:|
| Control | 12/25 | 37 | — |
| No one-ply | 16/24 | 40 | 3.21 |

The variant lost three moves over the first two games (16 versus 12 on seed
101003, 24 versus 25 on seed 201006), so it was behind the control before the
selected seeds could be reached. The pass also crossed the 30-minute wall-clock
ceiling, so it was stopped after game 2 and was not promoted. The experimental
switch was reverted; the accepted baseline remains unchanged.

## Mate-only override (adopted)

The per-move trace showed the selector was overriding the engine's root-best
move during long no-mate phases: 14 of 25 moves on seed 201006 and 13 of 28 on
seed 401012, including 10 and 12 overrides with no forced mate visible. The
adopted lever keeps the root-best move whenever no candidate sees a forced
mate, while still taking any candidate that does see one.

The two-seed screen (seeds 101003 and 401012, with games 2-3 as the hash-state
prefix) scored **19/13 = 32** versus the control **12/28 = 40**. The full run
used the same fixed depths, MultiPV 4/1, Threads 1, and **MateOnlyOverride=true**.

| Seed | Baseline | MateOnlyOverride |
|---:|---:|---:|
| 101003 | 12 | 19 |
| 201006 | 25 | 19 |
| 301009 | 19 | 21 |
| 401012 | 28 | 13 |
| 501015 | 23 | 7 |
| 601018 | 27 | 16 |
| 701021 | 17 | 26 |
| 801024 | 19 | 22 |
| 901027 | 17 | 30 |
| 1001030 | 7 | 18 |
| 1101033 | 23 | 26 |
| 1201036 | 18 | 17 |

- **Mean: 19.50 moves to mate** (baseline 19.58)
- **Wins: 12/12**
- **Total White moves: 234**
- **Game time: 830.16 s, about 3.55 s per White move**
- The full run completed under a 870 s hard cutoff with a 180 s per-game
  timeout; no game timed out.

The accepted configuration is root 18 / leaf 15 / deep root 18, MultiPV 4 /
deep MultiPV 1, Threads 1, **MateOnlyOverride true**. The default remains false
for compatibility; the benchmark flag is `--kestrel-mate-only-override` and the
UCI option is `MateOnlyOverride`.
