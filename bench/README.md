# Mate-speed benchmark

`mate_vs_vala.py` compares two selectors against the **same Maia-3 opponent**:

- **Kestrel mate-aware**: `mate/kestrel_mate.py`, Maia-3 reply model,
  mate-distance ranking.
- **Vala**: the real `vala.bot.vala_move` selector from a local Vala checkout.

Both arms play White from the standard start position. Maia-3 at the requested
Elo plays Black by sampling its policy. Each game seed is reused across arms, so
the opponent model and random stream are matched as closely as the different
move sequences allow.

## Why Vala uses the Kestrel binary

Vala's vendored `bin/patricia` is a Linux ELF binary and cannot run on this
Windows host. The benchmark passes the Kestrel/Patricia 5.1 binary to Vala's
`PatriciaPool`, so Vala's real selector and Kestrel's selector use the same
search engine. This measures the selection layer, not a difference between two
engine builds.

## Run

From the Checky workspace, using Vala's environment:

```bash
.cache/src/vala/.venv/Scripts/python.exe \
  kestrel/bench/mate_vs_vala.py --games 12 --arms kestrel,vala \
  --out out/kestrel-mate-12
```

Deep mate-distance mode:

```bash
.cache/src/vala/.venv/Scripts/python.exe \
  kestrel/bench/mate_vs_vala.py --games 12 --arms kestrel \
  --kestrel-root-ms 500 --kestrel-leaf-ms 300 \
  --kestrel-deep --kestrel-deep-root-ms 500 \
  --out out/kestrel-deep
```

Deterministic fixed-depth run:

```bash
.cache/src/vala/.venv/Scripts/python.exe \
  kestrel/bench/mate_vs_vala.py --games 12 --arms kestrel \
  --kestrel-root-depth 18 --kestrel-leaf-depth 15 \
  --kestrel-deep-root-depth 18 --kestrel-threads 1 \
  --kestrel-multipv 4 --kestrel-deep --kestrel-deep-multipv 1 \
  --kestrel-override-min-cp 50 \
  --kestrel-late-after 12 --kestrel-late-override-min-cp 55 \
  --out out/kestrel-det-12
```

`out/` is generated evidence and is not committed.

By default the harness starts a fresh Kestrel process before every game, so
search hash does not carry between seeds and each game is independently
reproducible. This is now the accepted protocol. Pass
`--no-kestrel-reset-per-game` only to reproduce the older cross-game-hash runs.

## Metric

`moves_to_mate` is the number of White moves in a won game. A loss, draw,
unfinished game, or error is not counted as a fast mate. The report also prints
the paired mean difference for seeds where both arms won.

## Result

See [`RESULTS.md`](RESULTS.md). The current accepted fixed-depth protocol, with
a fresh engine per game and a 50-to-55 cp late threshold switch, totals **198
moves over the 12 fixed seeds** (mean **16.50**), with 12/12 wins. The older
18.58 wall-clock comparison was a small legacy sample and is retained only as
history, not as a rating claim.
