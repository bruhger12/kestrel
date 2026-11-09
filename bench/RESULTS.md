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
mate-speed result on one opponent model, one time setting, and 12 games. The
C++ release binary remains the Patricia 5.1 baseline; this result belongs to
the experimental Python UCI front-end in `mate/`.
