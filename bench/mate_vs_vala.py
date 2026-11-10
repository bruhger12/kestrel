"""Compare Kestrel's mate-aware selector with Vala against the same Maia-3.

Both engines play White from the standard start position; Maia-3 at ``--opp-elo``
plays Black by sampling its policy.  Each game seed is reused for every arm, so
the opponent model and the random stream are matched as closely as possible.
The score is moves-to-mate on wins, not centipawns and not raw strength.

Run from the Checky workspace with Vala's environment:

    .cache/src/vala/.venv/Scripts/python.exe \
      kestrel/bench/mate_vs_vala.py --games 8 --arms kestrel,vala

This is an experimental harness, not a release binary.  It intentionally imports
Vala from ``--vala-root`` so the Vala side is the project's real selector, not a
reimplementation.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import chess

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KESTREL = ROOT / "kestrel" / "bin" / "windows-x86_64" / "kestrel-0.1.0-avx2.exe"
DEFAULT_VALA = ROOT / ".cache" / "src" / "vala"


@dataclass
class Row:
    arm: str
    game: int
    seed: int
    result: str
    plies: int
    white_moves: int
    moves_to_mate: int | None
    seconds: float
    first_move: str | None
    error: str | None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--games", type=int, default=8)
    p.add_argument("--start-game", type=int, default=1)
    p.add_argument("--arms", default="kestrel,vala")
    p.add_argument("--kestrel", type=Path, default=DEFAULT_KESTREL)
    p.add_argument("--vala-root", type=Path, default=DEFAULT_VALA)
    p.add_argument("--opp-elo", type=int, default=1500)
    p.add_argument("--seed", type=int, default=1000)
    p.add_argument("--max-plies", type=int, default=180)
    p.add_argument("--game-timeout", type=float, default=None)
    p.add_argument("--move-log", type=Path, default=None)
    p.add_argument("--kestrel-root-ms", type=int, default=500)
    p.add_argument("--kestrel-leaf-ms", type=int, default=300)
    p.add_argument("--kestrel-multipv", type=int, default=4)
    p.add_argument("--kestrel-deep", action="store_true")
    p.add_argument("--kestrel-deep-multipv", type=int, default=1)
    p.add_argument("--kestrel-override-min-cp", type=int, default=50)
    p.add_argument("--kestrel-late-after", type=int, default=12)
    p.add_argument("--kestrel-late-override-min-cp", type=int, default=55)
    p.add_argument("--kestrel-deep-root-ms", type=int, default=300)
    p.add_argument("--kestrel-root-depth", type=int, default=None)
    p.add_argument("--kestrel-leaf-depth", type=int, default=None)
    p.add_argument("--kestrel-deep-root-depth", type=int, default=None)
    p.add_argument("--kestrel-threads", type=int, default=8)
    p.add_argument(
        "--kestrel-reset-per-game",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    p.add_argument("--vala-cand-ms", type=int, default=120)
    p.add_argument("--vala-leaf-ms", type=int, default=35)
    p.add_argument("--vala-vala-ms", type=int, default=35)
    p.add_argument("--vala-pool", type=int, default=8)
    p.add_argument("--out", type=Path, default=ROOT / "out" / "kestrel-mate")
    return p.parse_args()


def maia_top(model, board: chess.Board, elo: int) -> chess.Move | None:
    probs, _ = model.predict(board, elo, elo)
    for uci, _p in sorted(probs.items(), key=lambda kv: -kv[1]):
        try:
            move = chess.Move.from_uci(uci)
        except ValueError:
            continue
        if move in board.legal_moves:
            return move
    return None


def play_game(
    arm: str,
    game: int,
    seed: int,
    *,
    model,
    kestrel,
    vala,
    opp_elo: int,
    max_plies: int,
    move_log=None,
    game_timeout: float | None = None,
) -> Row:
    board = chess.Board()
    rng = random.Random(seed)
    started = time.perf_counter()
    error: str | None = None
    white_moves = 0

    while not board.is_game_over(claim_draw=True) and board.move_stack.__len__() < max_plies:
        if game_timeout is not None and time.perf_counter() - started > game_timeout:
            error = "game timeout"
            break
        if board.turn == chess.WHITE:
            try:
                if arm.startswith("kestrel"):
                    choice = kestrel.choose(board, model, human_elo=opp_elo)
                    move = choice.move if choice else None
                elif arm == "vala":
                    move, _info = vala(board)
                else:
                    raise ValueError(f"unknown arm {arm!r}")
            except Exception as exc:  # keep one failed game from killing the run
                error = repr(exc)
                break
            if move is None:
                error = "no move"
                break
            if move not in board.legal_moves:
                error = f"illegal move {move.uci()}"
                break
            board.push(move)
            white_moves += 1
            if move_log is not None:
                entry = {
                    "game": game,
                    "seed": seed,
                    "ply": len(board.move_stack),
                    "side": "white",
                    "move": move.uci(),
                    "white_moves": white_moves,
                    "elapsed": round(time.perf_counter() - started, 3),
                    "trace": getattr(kestrel, "last_trace", None),
                }
                move_log.write(json.dumps(entry, sort_keys=True) + "\n")
                move_log.flush()
        else:
            move = model.sample(board, opp_elo, opp_elo, rng=rng, temperature=1.0)
            if move is None:
                error = "Maia returned no move"
                break
            board.push(move)
            if move_log is not None:
                entry = {
                    "game": game,
                    "seed": seed,
                    "ply": len(board.move_stack),
                    "side": "black",
                    "move": move.uci(),
                    "white_moves": white_moves,
                    "elapsed": round(time.perf_counter() - started, 3),
                }
                move_log.write(json.dumps(entry, sort_keys=True) + "\n")
                move_log.flush()

    if error is not None:
        result = "error"
    elif board.is_checkmate():
        result = "win" if board.turn == chess.BLACK else "loss"
    elif board.is_game_over(claim_draw=True):
        result = "draw"
    else:
        result = "unfinished"

    first = board.move_stack[0].uci() if board.move_stack else None
    return Row(
        arm=arm,
        game=game,
        seed=seed,
        result=result,
        plies=len(board.move_stack),
        white_moves=white_moves,
        moves_to_mate=white_moves if result == "win" else None,
        seconds=round(time.perf_counter() - started, 2),
        first_move=first,
        error=error,
    )


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def summary(rows: list[Row]) -> str:
    lines = ["# Kestrel mate-aware vs Vala", ""]
    lines.append("Both arms play White against Maia-3; lower moves-to-mate is better.")
    lines.append("")
    lines.append("| Arm | n | Wins | Losses | Draws | Errors | Mean moves | Median | Best | Worst |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for arm in sorted({r.arm for r in rows}):
        rs = [r for r in rows if r.arm == arm]
        wins = [r.moves_to_mate for r in rs if r.result == "win" and r.moves_to_mate is not None]
        lines.append(
            f"| {arm} | {len(rs)} | {len(wins)} | "
            f"{sum(r.result == 'loss' for r in rs)} | "
            f"{sum(r.result == 'draw' for r in rs)} | "
            f"{sum(r.result == 'error' for r in rs)} | "
            f"{mean(wins):.2f} | {statistics.median(wins) if wins else '—'} | "
            f"{min(wins) if wins else '—'} | {max(wins) if wins else '—'} |"
        )

    k_arm = "kestrel-deep" if any(r.arm == "kestrel-deep" for r in rows) else "kestrel"
    k = [r for r in rows if r.arm == k_arm and r.result == "win" and r.moves_to_mate is not None]
    v = [r for r in rows if r.arm == "vala" and r.result == "win" and r.moves_to_mate is not None]
    paired = [(a.moves_to_mate, b.moves_to_mate) for a in k for b in v if a.seed == b.seed]
    if paired:
        diffs = [a - b for a, b in paired]
        lines.append("")
        lines.append(
            f"Paired wins: {len(paired)} · mean Kestrel - Vala "
            f"{mean(diffs):+.2f} moves (negative is better) · "
            f"Kestrel {mean([a for a, _ in paired]):.2f} · "
            f"Vala {mean([b for _, b in paired]):.2f}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    jsonl = args.out / "games.jsonl"
    move_log = None
    if args.move_log is not None:
        args.move_log.parent.mkdir(parents=True, exist_ok=True)
        move_log = args.move_log.open("w", encoding="utf-8")

    sys.path.insert(0, str(args.vala_root))
    from vala.bot import vala_move
    from vala.maia import make_predictor
    from vala.pool import PatriciaPool

    sys.path.insert(0, str(ROOT / "kestrel" / "mate"))
    from kestrel_mate import KestrelMate

    print(f"loading Maia-3 (CPU) from {args.vala_root}", flush=True)
    model = make_predictor("maia3-5m", device="cpu")

    def make_kestrel() -> KestrelMate:
        return KestrelMate(
            str(args.kestrel),
            root_ms=args.kestrel_root_ms,
            leaf_ms=args.kestrel_leaf_ms,
            multipv=args.kestrel_multipv,
            deep=args.kestrel_deep,
            deep_multipv=args.kestrel_deep_multipv,
            override_min_cp=args.kestrel_override_min_cp,
            late_after=args.kestrel_late_after,
            late_override_min_cp=args.kestrel_late_override_min_cp,
            deep_root_ms=args.kestrel_deep_root_ms,
            root_depth=args.kestrel_root_depth,
            leaf_depth=args.kestrel_leaf_depth,
            deep_root_depth=args.kestrel_deep_root_depth,
            threads=args.kestrel_threads,
        )

    kestrel = None
    vala = None
    pool = None
    try:
        if "kestrel" in args.arms:
            kestrel = make_kestrel()
        if "vala" in args.arms:
            pool = PatriciaPool(n=args.vala_pool, path=str(args.kestrel))
            vala = lambda board: vala_move(
                board,
                pool,
                model,
                profile="balanced",
                human_elo=args.opp_elo,
                cand_ms=args.vala_cand_ms,
                leaf_ms=args.vala_leaf_ms,
                vala_ms=args.vala_vala_ms,
            )

        rows: list[Row] = []
        for game in range(args.start_game, args.games + 1):
            if (
                args.kestrel_reset_per_game
                and game > args.start_game
                and kestrel is not None
            ):
                kestrel.close()
                kestrel = make_kestrel()
            seed = args.seed + game * 100003
            for arm in [a.strip() for a in args.arms.split(",") if a.strip()]:
                label = "kestrel-deep" if args.kestrel_deep else "kestrel"
                display_arm = label if arm == "kestrel" else arm
                print(f"[{display_arm}] game {game}/{args.games} seed={seed}", flush=True)
                row = play_game(
                    display_arm,
                    game,
                    seed,
                    model=model,
                    kestrel=kestrel,
                    vala=vala,
                    opp_elo=args.opp_elo,
                    max_plies=args.max_plies,
                    move_log=move_log,
                    game_timeout=args.game_timeout,
                )
                rows.append(row)
                with jsonl.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(asdict(row), sort_keys=True) + "\n")
                print(
                    f"  {row.result} {row.plies} plies"
                    + (f" mate {row.moves_to_mate}" if row.moves_to_mate is not None else "")
                    + (f" error={row.error}" if row.error else "")
                    + f" {row.seconds:.1f}s",
                    flush=True,
                )
    finally:
        if kestrel is not None:
            kestrel.close()
        if pool is not None:
            pool.close()
        if move_log is not None:
            move_log.close()

    report = summary(rows)
    (args.out / "summary.md").write_text(report, encoding="utf-8")
    print("\n" + report)


if __name__ == "__main__":
    main()
