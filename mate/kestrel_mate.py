"""Mate-aware move selection for Kestrel.

The selector is intentionally narrow: Kestrel generates a few MultiPV
candidates, Maia supplies the modeled reply to each candidate, and a short
Kestrel leaf search scores the resulting position.  A line is ranked by mate
distance first, then by centipawns.  This is the objective the normal engine
search does not expose: it is not trying to maximize expected value, and it is
not trying to play more human-like moves.

The class accepts any opponent model with a ``predict(board, elo_self, elo_oppo)``
method returning ``(move_probs, win_prob)``.  The benchmark passes a Maia-3
predictor; the UCI wrapper can pass the same object.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import chess
import chess.engine


class OpponentModel(Protocol):
    def predict(
        self, board: chess.Board, elo_self: int = 1500, elo_oppo: int = 1500
    ) -> tuple[dict[str, float], float]: ...


@dataclass(frozen=True)
class Choice:
    move: chess.Move
    mate: int | None
    cp: int | None
    reply: chess.Move | None
    root_best: chess.Move
    rank: tuple[int, int, int]
    policy: float = 0.0
    branch: str = ""


def top_model_reply(
    model: OpponentModel, board: chess.Board, elo: int
) -> tuple[chess.Move | None, float]:
    """The model's most likely legal reply and its raw probability."""
    probs, _ = model.predict(board, elo, elo)
    for uci, p in sorted(probs.items(), key=lambda kv: -kv[1]):
        try:
            move = chess.Move.from_uci(uci)
        except ValueError:
            continue
        if move in board.legal_moves:
            return move, float(p)
    return None, 0.0


def top_model_move(model: OpponentModel, board: chess.Board, elo: int) -> chess.Move | None:
    """The model's most likely legal reply at one position."""
    return top_model_reply(model, board, elo)[0]


def _leaf_score(
    engine: chess.engine.SimpleEngine,
    board: chess.Board,
    time_ms: int,
    depth: int | None = None,
) -> chess.engine.PovScore | None:
    limit = chess.engine.Limit(depth=depth) if depth else chess.engine.Limit(time=time_ms / 1000)
    info = engine.analyse(board, limit)
    score = info.get("score")
    return score.pov(chess.WHITE) if score is not None else None


class KestrelMate:
    """A one-ply Maia-aware, mate-distance-first selector.

    Parameters are deliberately explicit so a benchmark can hold the search
    budget constant across engines.
    """

    def __init__(
        self,
        engine_path: str,
        *,
        root_ms: int = 500,
        leaf_ms: int = 300,
        multipv: int = 4,
        deep: bool = False,
        deep_multipv: int = 1,
        override_min_cp: int | None = 50,
        late_after: int | None = 12,
        late_override_min_cp: int | None = 55,
        mid_after: int | None = 7,
        mid_before: int | None = 8,
        mid_override_min_cp: int | None = 45,
        deep_root_ms: int | None = None,
        root_depth: int | None = None,
        leaf_depth: int | None = None,
        deep_root_depth: int | None = None,
        threads: int = 8,
        hash_mb: int = 1024,
    ) -> None:
        self.root_ms = root_ms
        self.leaf_ms = leaf_ms
        self.multipv = max(1, multipv)
        self.deep = deep
        self.deep_multipv = max(1, deep_multipv)
        self.override_min_cp = override_min_cp
        self.late_after = late_after
        self.late_override_min_cp = late_override_min_cp
        self.mid_after = mid_after
        self.mid_before = mid_before
        self.mid_override_min_cp = mid_override_min_cp
        self.deep_root_ms = deep_root_ms or root_ms
        self.root_depth = root_depth
        self.leaf_depth = leaf_depth
        self.deep_root_depth = deep_root_depth or root_depth
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.engine.configure({"Threads": threads, "Hash": hash_mb})
        self.last_trace: dict | None = None

    def close(self) -> None:
        self.engine.quit()

    def _candidates(
        self,
        board: chess.Board,
        *,
        time_ms: int | None = None,
        depth: int | None = None,
        multipv: int | None = None,
    ) -> list[tuple[chess.Move, int | None, int | None]]:
        limit = (
            chess.engine.Limit(depth=depth)
            if depth
            else chess.engine.Limit(time=(time_ms or self.root_ms) / 1000)
        )
        infos = self.engine.analyse(board, limit, multipv=multipv or self.multipv)
        out: list[tuple[chess.Move, int | None, int | None]] = []
        seen: set[chess.Move] = set()
        for info in infos:
            pv = info.get("pv") or []
            if not pv:
                continue
            move = pv[0]
            if move in seen:
                continue
            seen.add(move)
            score = info.get("score")
            if score is None:
                out.append((move, None, None))
                continue
            pov = score.pov(chess.WHITE)
            out.append((move, pov.mate(), pov.score()))
        return out

    def _leaf_rank(
        self, board: chess.Board
    ) -> tuple[tuple[int, int, int], int | None, int | None] | None:
        score = _leaf_score(self.engine, board, self.leaf_ms, self.leaf_depth)
        if score is None:
            return None
        mate = score.mate()
        cp = score.score()
        if mate is not None and mate > 0:
            rank = (0, mate, -(cp if cp is not None else 0))
        elif mate is not None:
            rank = (2, -mate, -(cp if cp is not None else 0))
        else:
            rank = (1, 0, -(cp if cp is not None else 0))
        return rank, mate, cp

    def choose(
        self,
        board: chess.Board,
        model: OpponentModel,
        *,
        human_elo: int = 1500,
    ) -> Choice | None:
        """Choose a move, or return None when the engine has no candidate."""
        candidates = self._candidates(board, depth=self.root_depth)
        if not candidates:
            self.last_trace = None
            return None

        root_best = candidates[0][0]
        ranked: list[Choice] = []
        for move, _root_mate, root_cp in candidates:
            after = board.copy()
            after.push(move)

            if after.is_checkmate():
                ranked.append(
                    Choice(
                        move, 0, root_cp, None, root_best,
                        (0, 0, -(root_cp or 0)), branch="immediate_mate",
                    )
                )
                continue
            if after.is_game_over():
                continue

            reply, policy = top_model_reply(model, after, human_elo)
            if reply is None:
                continue
            after_reply = after.copy()
            after_reply.push(reply)
            if after_reply.is_game_over():
                # After Maia's move it is White's turn.  A checkmate here means
                # White was mated; a draw is not a mate either.
                continue

            if self.deep:
                # Add one more our-move / Maia-reply pair before the leaf.  Keep
                # the one-ply result too: a deeper line that reports a longer
                # mate must not replace a shorter one.
                one_ply = self._leaf_rank(after_reply)
                deep_ranks: list[
                    tuple[tuple[int, int, int], int | None, int | None, str]
                ] = []
                if one_ply is not None:
                    deep_ranks.append((*one_ply, "one_ply_deep"))
                next_candidates = self._candidates(
                    after_reply,
                    time_ms=self.deep_root_ms,
                    depth=self.deep_root_depth,
                    multipv=self.deep_multipv,
                )
                for next_move, _next_mate, _next_cp in next_candidates:
                    after_next = after_reply.copy()
                    after_next.push(next_move)
                    if after_next.is_checkmate():
                        deep_ranks.append(((0, 0, 0), 0, 0, "deep_immediate"))
                        continue
                    if after_next.is_game_over():
                        continue
                    reply2 = top_model_move(model, after_next, human_elo)
                    if reply2 is None:
                        continue
                    after_reply2 = after_next.copy()
                    after_reply2.push(reply2)
                    if after_reply2.is_game_over():
                        continue
                    leaf = self._leaf_rank(after_reply2)
                    if leaf is not None:
                        deep_ranks.append((*leaf, "deep"))
                if deep_ranks:
                    rank, mate, cp, origin = min(deep_ranks, key=lambda item: item[0])
                    ranked.append(
                        Choice(
                            move, mate, cp, reply, root_best, rank, policy,
                            branch=origin,
                        )
                    )
                    continue

            leaf = self._leaf_rank(after_reply)
            if leaf is None:
                continue
            rank, mate, cp = leaf
            ranked.append(
                Choice(move, mate, cp, reply, root_best, rank, policy, branch="one_ply")
            )

        if not ranked:
            choice = Choice(root_best, None, None, None, root_best, (3, 0, 0), branch="fallback")
        else:
            choice = min(ranked, key=lambda c: c.rank)
            threshold = self.override_min_cp
            if (
                self.mid_override_min_cp is not None
                and self.mid_after is not None
                and self.mid_before is not None
                and self.mid_after <= board.fullmove_number <= self.mid_before
            ):
                threshold = self.mid_override_min_cp
            if (
                self.late_after is not None
                and self.late_override_min_cp is not None
                and board.fullmove_number >= self.late_after
            ):
                threshold = self.late_override_min_cp
            if threshold is not None and choice.mate is None:
                root_choice = next((c for c in ranked if c.move == root_best), None)
                no_mate = [c for c in ranked if c.mate is None and c.cp is not None]
                if root_choice is not None and no_mate:
                    best = max(no_mate, key=lambda c: c.cp)
                    gap = (best.cp or 0) - (root_choice.cp or 0)
                    if best is not root_choice and gap < threshold:
                        choice = root_choice
        self.last_trace = {
            "candidates": [
                {"move": move.uci(), "mate": mate, "cp": cp}
                for move, mate, cp in candidates
            ],
            "ranked": [
                {
                    "move": c.move.uci(),
                    "branch": c.branch,
                    "rank": list(c.rank),
                    "mate": c.mate,
                    "cp": c.cp,
                    "reply": c.reply.uci() if c.reply else None,
                    "policy": round(c.policy, 6),
                }
                for c in ranked
            ],
            "chosen": choice.move.uci(),
            "branch": choice.branch,
        }
        return choice
