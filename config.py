"""Shared configuration for local scripts, the API, and Airflow workers."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=False)


def project_path(name, default):
    path = Path(os.environ.get(name) or default).expanduser()
    return path if path.is_absolute() else ROOT / path


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "chessDB")
STOCKFISH_PATH = os.getenv("STOCKFISH_PATH", "stockfish")
PEOPLE_FILE = project_path("PEOPLE_FILE", "people.txt")
PGN_DATA_DIR = project_path("PGN_DATA_DIR", "PgnData")
OPENINGS_CSV = project_path("OPENINGS_CSV", "Data/openings.csv")


def read_people():
    """Missing roster produces no scheduled tasks until it is configured."""
    if not PEOPLE_FILE.exists():
        return []
    return list(dict.fromkeys(
        line.strip() for line in PEOPLE_FILE.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ))
