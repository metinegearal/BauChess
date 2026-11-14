"""Alternative local API; use this OR the Node backend on port 8000."""

import chess
import chess.engine
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pymongo import MongoClient

from config import MONGODB_URI, MONGODB_DATABASE, STOCKFISH_PATH, read_people

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "null"],
    allow_methods=["GET", "POST"], allow_headers=["Content-Type"],
)
client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
games = client[MONGODB_DATABASE]["games"]


class FenData(BaseModel):
    fen: str


class GameData(BaseModel):
    user: str
    date: str
    num: int = Field(ge=0)


@app.get("/users")
def users():
    return read_people() or games.distinct("User")


@app.post("/eval")
def evaluate_position(data: FenData):
    try:
        board = chess.Board(data.fen)
        if not board.is_valid():
            raise ValueError("Invalid position")
    except ValueError as error:
        raise HTTPException(400, "Invalid FEN") from error
    with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
        info = engine.analyse(board, chess.engine.Limit(time=0.1))
    return {"evaluation": info["score"].white().score(mate_score=100000)}


@app.post("/chart")
def chart(data: GameData):
    query = {"User": data.user, "Date": data.date.split("T")[0].replace("-", ".")}
    records = list(games.find(query).sort("game_id", 1).skip(data.num).limit(1))
    if not records:
        raise HTTPException(404, "No game found for this player, date, and index")
    output = records[0]
    return {key: output.get(key) for key in (
        "typeList", "evalList", "AverageTimePerMove", "TimePerMove", "Pgn", "UserColor"
    )}
