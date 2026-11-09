"""Maia-3 (Chessformer) opponent model for the Kestrel mate-aware mode.

This is a thin adapter over the ``maia3`` package.  Kestrel does not bundle the
model or the checkpoint; both are external research assets from CSSLab.  The
adapter only exposes the two methods the selector needs:

    predict(board, elo_self, elo_oppo) -> ({uci: probability}, win_probability)
    sample(board, elo_self, elo_oppo, rng, temperature) -> chess.Move | None

Maia-3: https://github.com/CSSLab/maia3
"""

from __future__ import annotations

from collections import deque
from types import SimpleNamespace

import chess

ELO_MIN, ELO_MAX = 600, 2600


class Maia3Opponent:
    def __init__(self, alias: str = "maia3-5m", device: str = "cpu") -> None:
        import torch
        from maia3.dataset import (
            get_historical_tokens,
            get_legal_moves_mask,
            tokenize_board,
        )
        from maia3.model_registry import (
            apply_model_config,
            resolve_checkpoint_path,
            resolve_model_spec,
        )
        from maia3.models import MAIA3Model
        from maia3.utils import get_all_possible_moves, mirror_move

        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"

        spec = resolve_model_spec(alias)
        cfg = SimpleNamespace(
            device=device,
            use_amp=False,
            trust_checkpoint=False,
            history=8,
            use_padding=True,
            include_time_info=False,
            dim_emb=128,
            dim_vit=192,
            num_blocks=8,
            num_heads=6,
            mlp_ratio=2.0,
            dropout=0.0,
            head_hid_dim=192,
            use_gab=True,
            gab_gen_size=64,
            gab_per_square_dim=0,
            gab_intermediate_dim=64,
            use_rms_norm=True,
            omit_qkv_biases=True,
            activation="gelu",
            use_relative_bias=False,
            use_absolute_pe=False,
        )
        apply_model_config(cfg, spec)
        cfg.checkpoint_path = resolve_checkpoint_path(spec)
        self.cfg = cfg
        self.device = device
        self._name = alias
        self._torch = torch
        self._tokenize_board = tokenize_board
        self._get_historical_tokens = get_historical_tokens
        self._get_legal_moves_mask = get_legal_moves_mask
        self._mirror_move = mirror_move
        self._all_moves = {m: i for i, m in enumerate(get_all_possible_moves())}

        model = MAIA3Model(cfg).to(device)
        checkpoint = torch.load(cfg.checkpoint_path, map_location=device, weights_only=True)
        state = checkpoint.get("model_state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint
        state = {k.replace("smolgen", "gab"): v for k, v in state.items()}
        model.load_state_dict(state, strict=False)
        model.eval()
        self._model = model

    @staticmethod
    def _clamp(elo: int) -> int:
        return max(ELO_MIN, min(ELO_MAX, int(elo)))

    def _history(self, board: chess.Board) -> deque:
        moves = list(board.move_stack)
        history: deque = deque(maxlen=self.cfg.history)
        replay = board.copy()
        for _ in moves:
            replay.pop()
        history.append(self._tokenize_board(replay))
        for move in moves:
            replay.push(move)
            history.append(self._tokenize_board(replay))
        return history

    def predict(
        self, board: chess.Board, elo_self: int = 1500, elo_oppo: int = 1500
    ) -> tuple[dict[str, float], float]:
        torch = self._torch
        if board.is_game_over():
            return {}, 0.5

        history = self._history(board)
        tokens = self._get_historical_tokens(
            history,
            self.cfg,
            base=0.0,
            inc=0.0,
            clk_left_before=0.0,
            clk_ponder=0.0,
        ).unsqueeze(0).to(self.cfg.device)
        mask = self._get_legal_moves_mask(board, self._all_moves).unsqueeze(0).to(self.cfg.device)
        self_elo = torch.tensor([self._clamp(elo_self)], dtype=torch.long, device=self.cfg.device)
        oppo_elo = torch.tensor([self._clamp(elo_oppo)], dtype=torch.long, device=self.cfg.device)

        with torch.no_grad():
            logits_move, logits_value, _ = self._model(tokens, self_elo, oppo_elo)
            probs = torch.softmax(logits_move.float().masked_fill(~mask, float("-inf")), dim=-1)[0].cpu()
            value = torch.softmax(logits_value.float(), dim=-1)[0, 2].item()

        out: dict[str, float] = {}
        for move in board.legal_moves:
            uci = move.uci()
            key = uci if board.turn == chess.WHITE else self._mirror_move(uci)
            idx = self._all_moves.get(key)
            if idx is not None:
                out[uci] = float(probs[idx])
        return out, float(value)

    def sample(
        self,
        board: chess.Board,
        elo_self: int = 1500,
        elo_oppo: int = 1500,
        *,
        rng=None,
        temperature: float = 1.0,
    ) -> chess.Move | None:
        import random

        rng = rng or random
        probs, _ = self.predict(board, elo_self, elo_oppo)
        if not probs:
            return None
        moves = list(probs)
        weights = [probs[m] ** (1.0 / max(1e-6, temperature)) for m in moves]
        total = sum(weights)
        if total <= 0:
            return chess.Move.from_uci(rng.choice(moves))
        point = rng.random() * total
        acc = 0.0
        for move, weight in zip(moves, weights):
            acc += weight
            if point <= acc:
                return chess.Move.from_uci(move)
        return chess.Move.from_uci(moves[-1])
