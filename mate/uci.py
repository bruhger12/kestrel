#!/usr/bin/env python3
"""UCI front-end for Kestrel's experimental mate-aware selector.

Standard UCI commands are accepted.  The engine loads Maia-3 lazily on the first
``isready`` so ``uci`` remains quick.  Kestrel itself remains the source of
search; this script only changes how a move is selected.

Example:

    printf 'uci\\nsetoption name Elo value 1500\\nisready\\nposition startpos\\ngo movetime 1000\\nquit\\n' \\
      | python mate/uci.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import chess

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from kestrel_mate import KestrelMate  # noqa: E402
from maia3_model import Maia3Opponent  # noqa: E402

ROOT = HERE.parent


def default_engine() -> Path:
    candidates = [
        ROOT / "bin" / "windows-x86_64" / "kestrel-0.1.0-avx2.exe",
        ROOT / "bin" / "windows-x86_64" / "kestrel-0.1.0-generic.exe",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("no Kestrel binary in bin/windows-x86_64")


def emit(line: str = "") -> None:
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def setoption(name: str, value: str, options: dict) -> None:
    if name == "Deep":
        options[name] = value.strip().lower() in {"true", "1", "yes"}
    elif name == "DeepMultiPV":
        try:
            options[name] = int(value)
        except ValueError:
            pass
    elif name in {
        "RootMs", "LeafMs", "MultiPV", "RootDepth", "LeafDepth",
        "DeepRootDepth", "Threads", "Hash", "Elo", "OverrideMinCp",
    }:
        try:
            options[name] = int(value)
        except ValueError:
            pass


def parse_position(words: list[str]) -> chess.Board:
    if not words:
        return chess.Board()
    if words[0] == "startpos":
        board = chess.Board()
        at = 1
    elif words[0] == "fen":
        if len(words) < 7:
            raise ValueError("bad FEN")
        board = chess.Board(" ".join(words[1:7]))
        at = 7
    else:
        raise ValueError(f"bad position prefix {words[0]!r}")
    if at < len(words):
        if words[at] != "moves":
            raise ValueError("expected moves")
        for uci in words[at + 1:]:
            board.push(chess.Move.from_uci(uci))
    return board


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, default=None)
    parser.add_argument("--maia", default="maia3-5m")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    options = {
        "RootMs": 500,
        "LeafMs": 300,
        "MultiPV": 4,
        "RootDepth": 0,
        "LeafDepth": 0,
        "DeepRootDepth": 0,
        "Threads": 8,
        "Hash": 1024,
        "Elo": 1500,
        "Deep": False,
        "DeepMultiPV": 1,
        "OverrideMinCp": 55,
    }
    board = chess.Board()
    engine: KestrelMate | None = None
    model: Maia3Opponent | None = None

    def ensure() -> None:
        nonlocal engine, model
        if engine is not None:
            return
        path = args.engine or default_engine()
        engine = KestrelMate(
            str(path),
            root_ms=options["RootMs"],
            leaf_ms=options["LeafMs"],
            multipv=options["MultiPV"],
            root_depth=options["RootDepth"] or None,
            leaf_depth=options["LeafDepth"] or None,
            deep_root_depth=options["DeepRootDepth"] or None,
            deep=options["Deep"],
            deep_multipv=options["DeepMultiPV"],
            override_min_cp=options["OverrideMinCp"],
            deep_root_ms=options["RootMs"],
            threads=options["Threads"],
            hash_mb=options["Hash"],
        )
        model = Maia3Opponent(args.maia, device=args.device)

    try:
        for raw in sys.stdin:
            line = raw.strip()
            if not line:
                continue
            words = line.split()
            cmd = words[0]

            if cmd == "uci":
                emit("id name Kestrel Mate 0.1")
                emit("id author Adam Kulju and Kestrel contributors")
                emit("option name RootMs type spin default 500 min 50 max 10000")
                emit("option name LeafMs type spin default 300 min 30 max 10000")
                emit("option name MultiPV type spin default 4 min 1 max 32")
                emit("option name RootDepth type spin default 0 min 0 max 64")
                emit("option name LeafDepth type spin default 0 min 0 max 64")
                emit("option name DeepRootDepth type spin default 0 min 0 max 64")
                emit("option name Threads type spin default 8 min 1 max 128")
                emit("option name Hash type spin default 1024 min 1 max 131072")
                emit("option name Elo type spin default 1500 min 600 max 2600")
                emit("option name Deep type check default false")
                emit("option name DeepMultiPV type spin default 1 min 1 max 16")
                emit("option name OverrideMinCp type spin default 55 min 0 max 1000000000")
                emit("uciok")
            elif cmd == "isready":
                ensure()
                emit("readyok")
            elif cmd == "setoption":
                if "name" in words:
                    name = words[words.index("name") + 1]
                    value = " ".join(words[words.index("value") + 1:]) if "value" in words else ""
                    setoption(name, value, options)
            elif cmd == "ucinewgame":
                board = chess.Board()
            elif cmd == "position":
                try:
                    board = parse_position(words[1:])
                except (ValueError, chess.InvalidMoveError) as exc:
                    sys.stderr.write(f"[kestrel-mate] bad position: {exc}\n")
            elif cmd == "go":
                ensure()
                assert engine is not None and model is not None
                budget = 1000
                if "movetime" in words:
                    try:
                        budget = max(50, int(words[words.index("movetime") + 1]))
                    except (ValueError, IndexError):
                        pass
                engine.root_ms = max(50, int(budget * 0.5))
                engine.leaf_ms = max(30, int(budget * 0.3))
                choice = engine.choose(board, model, human_elo=options["Elo"])
                emit(f"bestmove {choice.move.uci() if choice else '0000'}")
            elif cmd == "stop":
                pass
            elif cmd == "quit":
                break
    finally:
        if engine is not None:
            engine.close()


if __name__ == "__main__":
    main()
