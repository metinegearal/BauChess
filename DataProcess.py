"""Turn a scraped PGN (with an optional timestamp copy) into a game record."""

import hashlib
import io
import re

import chess
import chess.pgn

from StockFishReview import stockfishDataProcess


def processGames(user, pgn):
    if not pgn.strip():
        return {}
    main, _, timed = pgn.partition(" ***TimeStamp*** ")
    game = chess.pgn.read_game(io.StringIO(main.strip()))
    if game is None or game.errors:
        raise ValueError("Invalid PGN")
    output = dict(game.headers)
    if user.lower() == output.get("White", "").lower():
        color = chess.WHITE
    elif user.lower() == output.get("Black", "").lower():
        color = chess.BLACK
    else:
        raise ValueError(f"{user} is not a player in this game")

    times = []
    timed_game = chess.pgn.read_game(io.StringIO(timed.strip())) if timed.strip() else game
    if timed_game is not None:
        for node in timed_game.mainline():
            timestamp = re.search(r"\[%timestamp (\d+)\]", node.comment)
            if node.parent.board().turn == color:
                times.append(int(timestamp.group(1)) / 10 if timestamp else None)

    known_times = [value for value in times if value is not None]
    if not known_times:
        times = []

    # Each game can have a separate review for both players.
    identity = output.get("Link") or game.end().board().fen() + str(sorted(output.items()))
    game_id = hashlib.sha256((user.lower() + ":" + identity).encode()).hexdigest()
    output.update({
        "Pgn": game.accept(chess.pgn.StringExporter(headers=True, variations=False, comments=False)),
        "User": user,
        "UserColor": "White" if color else "Black",
        "TimePerMove": times,
        "AverageTimePerMove": sum(known_times) / len(known_times) if known_times else 0,
        "game_id": game_id,
    })
    output.update(stockfishDataProcess(output["Pgn"], output["UserColor"].lower()))
    return output
