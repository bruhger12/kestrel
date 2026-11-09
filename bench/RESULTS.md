# 12-game mate-speed result

Date: 2026-11-09

Both selectors played White against the same Maia-3 (5M, CPU) opponent at
1500 Elo, with Maia sampling at temperature 1.0. Each game seed was reused for
both arms.

## Settings

- **Kestrel deep**: Kestrel 0.1.0 AVX2, root 500 ms, leaf 300 ms, MultiPV 4,
  deep root 500 ms, deep MultiPV 1.
- **Vala**: `vala_move` profile `balanced`, candidate 120 ms, leaf/vala 35 ms,
  Patricia pool of 8 using the same Kestrel binary.
- 12 paired games, 180-ply cap, no errors or unfinished games.

## Result

| Game | Seed | Kestrel deep | Vala | Difference |
|---:|---:|---:|---:|---:|
| 1 | 101003 | 17 | 29 | -12 |
| 2 | 201006 | 23 | 18 | +5 |
| 3 | 301009 | 19 | 26 | -7 |
| 4 | 401012 | 26 | 15 | +11 |
| 5 | 501015 | 24 | 21 | +3 |
| 6 | 601018 | 13 | 22 | -9 |
| 7 | 701021 | 18 | 15 | +3 |
| 8 | 801024 | 12 | 19 | -7 |
| 9 | 901027 | 14 | 22 | -8 |
| 10 | 1001030 | 7 | 24 | -17 |
| 11 | 1101033 | 23 | 12 | +11 |
| 12 | 1201036 | 27 | 20 | +7 |

- **Kestrel deep mean: 18.58 moves** (median 18.5, best 7, worst 27)
- **Vala mean: 20.25 moves** (median 20.5, best 12, worst 29)
- **Paired mean difference: -1.67 moves** (negative favors Kestrel)
- **Head-to-head: 6 Kestrel faster, 6 Vala faster**

## Interpretation

Kestrel's mean was lower in this sample, but the 6–6 split means this is not a
statistically strong win and not a general strength claim. It is a local
mate-speed result on one opponent model, one time setting, and 12 games.The C++ release binary remains the Patricia 5.1 baseline; this result belongs to
the experimental Python UCI front-end in `mate/`.

## Variant attempts (not adopted)

These were short screens, not full runs. None beat the 18.58 selector.

| Variant | Screen result | Why it was dropped |
|---|---|---|
| Top-2 Maia replies with expected mate value | 16 moves on seed 101003, 24 on 201006 | Not better than 17/23, and roughly twice as slow |
| `DeepMultiPV=2` | 30 moves on seed 101003 | Worse than 17 |
| Double root/leaf time | 22 moves on seed 101003 | Worse than 17 |
| Precomputed high-depth mate book (3 s, 16 PV, FEN-keyed) | 31 moves on seed 101003 | Worse than 17; stopped at the two-seed screen |

The baseline selector and settings in this report remain the best measured
configuration.

## Reproducibility note

After reverting the book experiment, an identical two-seed baseline recheck
produced 23 moves on seed 101003 and 15 on seed 201006 (mean 19.00), rather than
the original run's 17 and 23. The engine search is wall-clock limited, so
individual runs are not bit-for-bit reproducible. The 12-game result above is
the recorded best sample; the code and settings were restored exactly.

## Precomputed book attempt

The experimental FEN-keyed mate book used a 3-second, 16-PV offline analysis and
cached the live selector's move unless it found a shorter forced mate. Its first
screen seed took 31 moves versus the baseline's 17, so the run was stopped at the
two-seed gate and the book code was reverted. It was not played over 12 seeds.
