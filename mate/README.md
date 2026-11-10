# Kestrel Mate (experimental)

`mate/` is a Python UCI front-end for the mate-distance objective. It is **not**
part of the checked-in `kestrel-0.1.0-avx2.exe` binary, and it is not a release
artifact.

## What it does

For each move:

1. Kestrel searches a small MultiPV set.
2. Maia-3 predicts the modeled opponent's most likely reply to each candidate.
3. Kestrel evaluates the resulting position for a short time.
4. The candidate with the shortest forced mate wins; otherwise centipawns break
   the tie.

The opponent model is used only for planning. The actual opponent can be a
human, another engine, or Maia sampling moves.

## Requirements

- The Kestrel binary at `bin/windows-x86_64/kestrel-0.1.0-avx2.exe`
- Python 3.11 or 3.12
- The external Maia-3 package and checkpoint

```bash
python -m venv .venv
.venv/Scripts/pip install -r mate/requirements.txt
```

The first Maia-3 run downloads its checkpoint. Kestrel does not bundle the
model, and the model is not covered by this repository's MIT license.

## Run

```bash
python mate/uci.py
```

UCI options:

| Option | Default | Meaning |
| --- | --- | --- |
| `RootMs` | 500 | Kestrel MultiPV root budget (ignored when `RootDepth` is set) |
| `LeafMs` | 300 | Kestrel leaf evaluation budget (ignored when `LeafDepth` is set) |
| `RootDepth` | 0 | Fixed root depth; `0` uses `RootMs` |
| `LeafDepth` | 0 | Fixed leaf depth; `0` uses `LeafMs` |
| `DeepRootDepth` | 0 | Fixed deep root depth; `0` uses `RootDepth` |
| `MultiPV` | 4 | Candidate moves |
| `Threads` | 8 | Kestrel search threads |
| `Hash` | 1024 | Kestrel hash in MB |
| `Elo` | 1500 | Rating passed to Maia-3 |
| `Deep` | false | Add one more our-move/Maia-reply pair before the leaf |
| `DeepMultiPV` | 1 | Next-move candidates in deep mode |
| `OverrideMinCp` | 50 | Minimum leaf-centipawn gap required to override root-best when no forced mate is visible |
| `EarlyAfter` | 4 | First fullmove of the early override window |
| `EarlyBefore` | 4 | Last fullmove of the early override window |
| `EarlyOverrideMinCp` | 45 | Override threshold inside the early window |
| `MicroAfter` | 5 | First fullmove of the micro override window |
| `MicroBefore` | 5 | Last fullmove of the micro override window |
| `MicroOverrideMinCp` | 56 | Override threshold inside the micro window |
| `MidAfter` | 7 | First fullmove of the mid-game override window |
| `MidBefore` | 8 | Last fullmove of the mid-game override window |
| `MidOverrideMinCp` | 45 | Override threshold inside the mid-game window |
| `PrelateAfter` | 11 | First fullmove of the pre-late override window |
| `PrelateBefore` | 11 | Last fullmove of the pre-late override window |
| `PrelateOverrideMinCp` | 103 | Override threshold inside the pre-late window |
| `LateAfter` | 12 | Fullmove number where the late override threshold begins |
| `LateOverrideMinCp` | 55 | Override threshold from `LateAfter` onward |

`go movetime N` temporarily scales `RootMs` to `0.5N` and `LeafMs` to `0.3N`.

## Limit

The default mode is a one-ply opponent model. `Deep=true` adds a second
our-move/Maia-reply pair. In the 12-game local harness, deep mode averaged
18.58 moves to mate versus Vala's 20.25 (paired difference −1.67, but 6–6 on
individual games). That is a small-sample result, not a claim that the selector
is stronger than Vala in every position or time control. See
[`../bench/RESULTS.md`](../bench/RESULTS.md) for the exact result and settings.
