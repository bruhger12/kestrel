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
  --out out/kestrel-det-12
```

`out/` is generated evidence and is not committed.

## Metric

`moves_to_mate` is the number of White moves in a won game. A loss, draw,
unfinished game, or error is not counted as a fast mate. The report also prints
the paired mean difference for seeds where both arms won.

## Result

See [`RESULTS.md`](RESULTS.md). In the 12-game deep run, Kestrel averaged 18.58
moves to mate versus Vala's 20.25 (paired difference -1.67), with a 6-6 split on
individual games. That is a small-sample local result, not a rating claim.
