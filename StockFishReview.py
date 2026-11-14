"""Stockfish move analysis and per-player review summaries."""

import io
import os

import chess
import chess.engine
import chess.pgn

from ChessTools import accuracy, classify_move, cp_to_ep, find_opening
from config import STOCKFISH_PATH


def get_phase(board, move_number):
    values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
    material = sum((len(board.pieces(piece, True)) + len(board.pieces(piece, False))) * value
                   for piece, value in values.items())
    queens = board.pieces(chess.QUEEN, True) or board.pieces(chess.QUEEN, False)
    if move_number <= 12 and queens:
        return 'Opening'
    return 'Endgame' if not queens or material <= 40 else 'Middlegame'


def analyze_pgn_with_stockfish(pgn_text, engine_path=STOCKFISH_PATH, depth=None):
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None or game.errors:
        raise ValueError('Invalid PGN')
    board = game.board()
    analysis = []
    depth = depth or int(os.getenv('STOCKFISH_DEPTH', '12'))
    with chess.engine.SimpleEngine.popen_uci(engine_path) as engine:
        engine.configure({'Threads': int(os.getenv('STOCKFISH_THREADS', '2')),
                          'Hash': int(os.getenv('STOCKFISH_HASH_MB', '128'))})
        for index, move in enumerate(game.mainline_moves(), 1):
            before = engine.analyse(board, chess.engine.Limit(depth=depth))
            eval_before = before['score'].white().score(mate_score=10000)
            san = board.san(move)
            pv = board.san(before['pv'][0]) if before.get('pv') else 'Finished'
            captured = board.piece_at(move.to_square) if board.is_capture(move) else None
            if board.is_en_passant(move):
                captured = chess.Piece(chess.PAWN, not board.turn)
            board.push(move)
            after = engine.analyse(board, chess.engine.Limit(depth=depth))
            eval_after = after['score'].white().score(mate_score=10000)
            analysis.append({
                'move': san, 'captured_piece': captured.symbol() if captured else 'None',
                'fen': board.fen(), 'phase': get_phase(board, index),
                'eval_before': eval_before, 'eval_after': eval_after,
                'eval_diff': eval_after - eval_before, 'pv': pv,
            })
    return analysis


def stockfishDataProcess(pgn_text, player):
    if player.lower() not in ('white', 'black'):
        raise ValueError('Player must be white or black')
    summary = dict.fromkeys(('total_moves', 'best', 'excellent', 'good', 'blunder', 'mistake', 'inaccuracy'), 0)
    phase_losses = {phase: [] for phase in ('Opening', 'Middlegame', 'Endgame')}
    losses, types, centipawns = [], [], []
    analysis = analyze_pgn_with_stockfish(pgn_text)
    # Parsed PGN may begin with Black to move in a custom starting position.
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    turn = game.board().turn
    selected = player.lower() == 'white'
    for row in analysis:
        if turn == selected:
            sign = 1 if turn == chess.WHITE else -1
            before, after = sign * row['eval_before'], sign * row['eval_after']
            loss = max(0, cp_to_ep(before) - cp_to_ep(after))
            label = classify_move(before, after)
            types.append(label)
            losses.append(loss)
            phase_losses[row['phase']].append(loss)
            centipawns.append(max(0, before - after))
            summary[label] += 1
            summary['total_moves'] += 1
        turn = not turn
    return {
        'summary': summary, 'accuracy': accuracy(losses),
        'phases': {phase: accuracy(values) for phase, values in phase_losses.items()},
        'opening': find_opening(pgn_text), 'evalList': [row['eval_after'] for row in analysis],
        'typeList': types, 'centipawnLoseList': centipawns,
    }
