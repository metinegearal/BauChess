"""Store game reviews and statistics safely across scheduled retries."""

from datetime import datetime
from statistics import mean

from pymongo import MongoClient

from config import MONGODB_DATABASE, MONGODB_URI


def insertData(username, data):
    if not data:
        return "no data"
    # Build the full stats record before writing either collection.
    losses = data["centipawnLoseList"]
    summary = data["summary"]
    color = data["UserColor"]
    stats = {
        "GameID": data["game_id"],
        "GameDate": datetime.strptime(data["Date"], "%Y.%m.%d"),
        "PlayerName": username,
        "TimePerMove": data["AverageTimePerMove"],
        "TotalTime": data.get("TimeControl", "?"),
        "NumMoves": summary["total_moves"],
        "Accuracy": data["accuracy"],
        "Blunders": summary["blunder"],
        "Mistakes": summary["mistake"],
        "Inaccuracies": summary["inaccuracy"],
        "AvgCentipawnLoss": mean(losses) if losses else 0,
        "MaxCentipawnLoss": max(losses, default=0),
        "UserElo": data.get(color + "Elo"),
        "OpponentElo": data.get(("Black" if color == "White" else "White") + "Elo"),
        "Opening": data["opening"],
        "Result": data["Result"],
        "Termination": data.get("Termination", ""),
        "User": username,
    }
    document = {key: value for key, value in data.items() if key != "_id"}
    document["User"] = username
    with MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000) as client:
        db = client[MONGODB_DATABASE]
        db.games.create_index("game_id", unique=True)
        db.stats.create_index("GameID", unique=True)
        db.games.update_one({"game_id": data["game_id"]}, {"$set": document}, upsert=True)
        db.stats.update_one({"GameID": data["game_id"]}, {"$set": stats}, upsert=True)
    return data["game_id"]
