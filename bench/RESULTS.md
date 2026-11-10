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

## Mate-only override (previous 19.50 baseline)

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

That binary rule produced the previous 19.50 result. It has now been replaced by
the centipawn threshold below; its full table is retained for comparison.

## Centipawn override threshold (adopted)

The binary rule is replaced by `OverrideMinCp`: when no candidate has a forced
mate, keep root-best unless the best leaf-centipawn candidate beats root-best's
leaf score by at least the threshold. The sweep tested **50 cp** and **100 cp**.
The 100 cp candidate was eliminated on the games 1-4 prefix: 21/21/33/21 = 96,
versus 72 for the 19.50 configuration. The 50 cp run completed all 12 games.

| Seed | 19.50 binary | 50 cp |
|---:|---:|---:|
| 101003 | 19 | 13 |
| 201006 | 19 | 18 |
| 301009 | 21 | 20 |
| 401012 | 13 | 22 |
| 501015 | 7 | 14 |
| 601018 | 16 | 20 |
| 701021 | 26 | 23 |
| 801024 | 22 | 21 |
| 901027 | 30 | 22 |
| 1001030 | 18 | 13 |
| 1101033 | 26 | 14 |
| 1201036 | 17 | 22 |

- **50 cp mean: 18.50 moves to mate** (previous 19.50)
- **Wins: 12/12**
- **Total White moves: 222** (previous 234)
- **Game time: 924.40 s, about 4.16 s per White move**
- The full run completed under a 1050 s hard cutoff with a 240 s per-game
  timeout; no game timed out.

The accepted configuration is root 18 / leaf 15 / deep root 18, MultiPV 4 /
deep MultiPV 1, Threads 1, **OverrideMinCp 50**. The benchmark flag is
`--kestrel-override-min-cp 50`; the UCI option is `OverrideMinCp=50`.

## Threshold sweep around 50 cp (no improvement)

Three additional full-12 measurements bracketed the incumbent. Every run won
all 12 games, used the same search shape and one thread, and completed within
its 300 s per-game timeout. The 100 cp point was screened earlier and is not a
full-12 candidate.

| Seed | 25 cp | 40 cp | **50 cp (chosen)** | 65 cp |
|---:|---:|---:|---:|---:|
| 101003 | 13 | 13 | **13** | 13 |
| 201006 | 22 | 18 | **18** | 18 |
| 301009 | 27 | 20 | **20** | 27 |
| 401012 | 23 | 22 | **22** | 36 |
| 501015 | 22 | 14 | **14** | 24 |
| 601018 | 24 | 20 | **20** | 15 |
| 701021 | 17 | 20 | **23** | 18 |
| 801024 | 19 | 23 | **21** | 22 |
| 901027 | 10 | 20 | **22** | 15 |
| 1001030 | 18 | 27 | **13** | 16 |
| 1101033 | 19 | 14 | **14** | 17 |
| 1201036 | 29 | 23 | **22** | 21 |
| **Total** | **243** | **234** | **222** | **242** |
| **Mean** | **20.25** | **19.50** | **18.50** | **20.17** |

No threshold beat the 50 cp result. The curve is not flat around it: 40 cp is
12 moves worse, 65 cp is 20 moves worse, and 25 cp is 21 moves worse. The 50 cp
configuration is therefore both the previous 18.50/222 best and the retained
choice; there is no side-by-side regression to adopt.

The slowest games were 115.15 s (25 cp), 119.55 s (40 cp), 127.08 s (50 cp),
and 125.39 s (65 cp), all well below the 300 s per-game timeout. All four
full-12 runs completed within the 1200 s hard cutoff. The 50 cp default is set
in `KestrelMate`, the benchmark flag, and the UCI option.

## Fine threshold checks and selector screens (no improvement)

A later full-12 pass filled in the two immediate neighbors and repeated the
incumbent. All games were wins and no game timed out:

| Threshold | Per-seed moves | Total | Mean |
|---:|---|---:|---:|
| 45 cp | 13/18/20/22/14/20/23/21/22/13/14/22 | 222 | 18.50 |
| 50 cp repeat | 13/18/20/22/14/20/23/21/22/13/14/22 | 222 | 18.50 |
| 55 cp | 13/18/20/22/14/20/23/21/22/12/20/20 | 225 | 18.75 |

45 cp is bit-identical to 50 cp, confirming a flat region between those two
points, and the repeated 50 cp run is exactly reproducible. 55 cp gains one
move on seed 1001030 but loses eight across seeds 1101033 and 1201036, so it is
not adopted. No threshold below 50 cp beat 18.50.

Three selector levers were screened and rejected without promotion:

- **MultiPV 3.** The full 12 seeds totaled **284**
  (23/21/39/38/27/29/21/15/16/12/20/23), mean **23.67**, with 12/12 wins.
  This is 62 moves worse than MultiPV 4 and was rejected.
- **MultiPV 5.** Nine completed seeds totaled **204**
  (22/24/20/28/30/20/30/14/16), mean **22.67**, versus 173 for the control's
  first nine. The run was then aborted; the remaining rows are manual-stop
  engine errors and are not treated as game results.
- **Policy tie-break for equal ranks.** First three seeds totaled 73
  (17/31/25), versus 51 (13/18/20). Stopped during game 4.

The horizon-adjusted deep comparison was run to completion because it is a
truthful normalization of mate distances measured one White move apart. Its
full-12 counts were identical to 50 cp: **13/18/20/22/14/20/23/21/22/13/14/22,
total 222, mean 18.50**, with 12/12 wins. It therefore changed no selected move
and was reverted rather than retained as dead configuration.

## Sampled-reply weighting (rejected after one seed)

The selector normally scores each root candidate against only Maia's single
most likely reply. This variant instead used Maia's top two legal replies with
their actual temperature-1.0 sampling probabilities. The first reply retained
the full deep line; the second used a one-ply leaf, adding one leaf search per
root candidate. Both no-mate lines were combined by probability-weighted
centipawns, both mating lines by probability-weighted mate distance, and a
mixed pair fell back to the worse line so a mate available only against one
reply was not treated as forced.

On seed 101003 the variant won in **22 moves**, versus **13** for the incumbent,
and took **89.90 s** versus **46.57 s** for the same seed. That is a clear
mate-count and wall-time regression, so the run was stopped after game 1. No
full-12 table exists for this arm; it was not adopted. The experimental source
was fully reverted.

## Mate-safe near-tie sampled reply (rejected after one seed)

This arm kept the existing single-reply deep score as the primary ranking. It
used Maia's second sampled reply only inside a same-bucket, same-mate window
with primary centipawns within **20 cp**, and only when the second reply had at
least **10%** probability and at least **35%** of the top reply's probability.
The second reply was priced as one leaf evaluation. Same-mate lines were
combined by probability-weighted mate distance; no-mate lines by weighted
centipawns. No deep search was duplicated.

On the first seed the arm won in **18 moves** versus **13** for the incumbent,
taking **62.64 s** versus **46.57 s**. Per White move that is 3.48 s versus
3.58 s, so the per-move cost did not regress materially; the move count did.
The run was stopped after game 1 and the partial second game was discarded.

Trace replay showed 18 near-tie decisions in the completed game, 8 with more
than one candidate, and 4 where the second reply was actually evaluated. The
near-tie result did not change the final move after the accepted 50 cp
threshold on any of those 18 moves. The extra leaf evaluations nevertheless
altered engine hash state, and the game diverged to a slower mate. This arm was
not adopted, no full-12 table exists, and the experimental source was fully
reverted.

## Low-confidence override gate at 25% (full 12; rejected)

The accepted threshold can replace root-best only when no candidate has a mate.
This screen adds a confidence gate: keep root-best when the selected no-mate
line's top Maia reply has probability below **25%**, even if its centipawn lead
is at least 50. The gate makes no additional engine calls.

| Seed | Accepted | 25% gate |
|---:|---:|---:|
| 101003 | 13 | 13 |
| 201006 | 18 | 18 |
| 301009 | 20 | **27** |
| 401012 | 22 | 20 |
| 501015 | 14 | 19 |
| 601018 | 20 | 18 |
| 701021 | 23 | 28 |
| 801024 | 21 | 14 |
| 901027 | 22 | 16 |
| 1001030 | 13 | **31** |
| 1101033 | 14 | 15 |
| 1201036 | 22 | 18 |
| **Total** | **222** | **237** |
| **Mean** | **18.50** | **19.75** |

The intended early stop killed the process wrapper but not the running child,
so all 12 games completed. The gate gained six moves on seed 8, six on seed 9,
four on seed 12, and smaller amounts elsewhere, but lost seven on seed 3, five
on seed 7, and eighteen on seed 10. All 12 games were wins with no errors. The
25% and 20% runs overlapped, so their wall times are not a clean cost
comparison; the fixed-depth move counts are the decision evidence. The 25%
gate was not adopted.

## Low-confidence override gate at 20% (full 12; rejected)

On the accepted 12-game trace, only one non-root override used a top Maia
reply below 20% probability: seed 9, move 14, at 16.98%. This screen keeps
root-best when the selected no-mate line is based on a reply below **20%**,
even when its centipawn lead clears 50. It makes no additional engine calls.

The complete run won all 12 games with no errors or timeouts:

| Seed | Accepted | 20% gate |
|---:|---:|---:|
| 101003 | 13 | 13 |
| 201006 | 18 | 18 |
| 301009 | 20 | 20 |
| 401012 | 22 | 22 |
| 501015 | 14 | 14 |
| 601018 | 20 | 20 |
| 701021 | 23 | 23 |
| 801024 | 21 | 21 |
| 901027 | 22 | **18** |
| 1001030 | 13 | **23** |
| 1101033 | 14 | **23** |
| 1201036 | 22 | **26** |
| **Total** | **222** | **241** |
| **Mean** | **18.50** | **20.08** |

The gate gained four moves on seed 9 but lost ten on seed 10, nine on seed 11,
and four on seed 12. Game 12 also changed its first move from `e2e4` to `g1f3`
after the seed-9 divergence altered engine hash state. Both gate runs overlapped
during collection, so their wall times are not comparable; the move totals are
the decision evidence. The 20% gate was not adopted, and both low-confidence
gate experiments were fully reverted. There is no repeat full-12 run because
neither first run met the adoption condition.

The accepted configuration remains root 18 / leaf 15 / deep root 18, MultiPV
4/1, Threads 1, and **OverrideMinCp 50**, at **222 total / 18.50 mean**.
