"""Daily extract → Stockfish analysis → MongoDB pipeline."""

from datetime import timedelta
import logging

import pendulum
from airflow.sdk import dag, task, TaskGroup

from config import read_people
from ScrapChessData import scrapChessData
from DataProcess import processGames
from DataStorage import insertData


@dag(
    "BauChess_Scrap_to_DB",
    schedule=timedelta(days=1),
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["BauChess"],
    default_args={"retries": 3, "retry_delay": timedelta(minutes=5)},
)
def BauChess_taskflow_api():
    @task(execution_timeout=timedelta(minutes=20))
    def extract(user):
        status, pgn = scrapChessData(user)
        logging.info("Extraction finished for %s: %s", user, status)
        return pgn

    @task(execution_timeout=timedelta(hours=2))
    def process(user, raw):
        return [
            processGames(user, game)
            for game in raw.split(" ***Space*** ") if game.strip()
        ]

    @task()
    def load(user, records):
        for record in records:
            insertData(user, record)
        logging.info("Stored %d game reviews for %s", len(records), user)

    for index, user in enumerate(read_people()):
        with TaskGroup(group_id=f"player_{index}"):
            load(user, process(user, extract(user)))


BauChess_taskflow_api()
