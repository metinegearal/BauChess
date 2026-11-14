"""Opening lookup and heuristic move-quality metrics."""

from functools import lru_cache
import io

import chess
import chess.pgn
import pandas as pd

from config import OPENINGS_CSV


def extract_moves(pgn_text, num_moves=6):
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        return []
    board = game.board()
    moves = []
    for move in list(game.mainline_moves())[:num_moves * 2]:
        moves.append(board.san(move))
        board.push(move)
    return moves


@lru_cache(maxsize=1)
def _openings():
    return pd.read_csv(OPENINGS_CSV)


def find_opening(pgn_text):
    moves = extract_moves(pgn_text)
    best, length = 'Opening not found', 0
    for _, row in _openings().iterrows():
        prefix = []
        for column in ('move1w', 'move1b', 'move2w', 'move2b', 'move3w', 'move3b', 'move4w', 'move4b'):
            if pd.isna(row[column]):
                break
            prefix.append(row[column])
        if len(prefix) > length and moves[:len(prefix)] == prefix:
            best, length = row['Opening'], len(prefix)
    return best


def cp_to_ep(cp):
    """Logistic expected-points estimate; not a platform's proprietary metric."""
    return 1 / (1 + 10 ** (-cp / 400))


def accuracy(losses):
    return 1 - sum(losses) / len(losses) if losses else None


def classify_move(eval_before, eval_after):
    """Inputs must be from the moving player's perspective."""
    loss = max(0, cp_to_ep(eval_before) - cp_to_ep(eval_after))
    for threshold, label in ((0, 'best'), (.02, 'excellent'), (.05, 'good'), (.10, 'inaccuracy'), (.20, 'mistake')):
        if loss <= threshold:
            return label
    return 'blunder'
