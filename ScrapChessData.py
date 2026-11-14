"""Collect the latest ten games through Chess.com's PGN export dialog."""

import datetime
import io
import os
import re

import chess.pgn
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import PGN_DATA_DIR, read_people

ROWS = "//*[@id='profile-main']/div/div[3]/div/table/tbody/tr"
SHARE_BUTTONS = (
    "//*[@id='board-layout-sidebar']/div[2]/div[6]/button[1]",
    "//*[@id='board-layout-sidebar']/div[2]/div[5]/button[1]",
)


def scrapChessData(name):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError("Invalid Chess.com username")
    after = os.getenv("SCRAPE_AFTER_DATE", "").strip()
    cutoff = datetime.date.fromisoformat(after) if after else None
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1000")
    if os.getenv("CHROME_BINARY"):
        options.binary_location = os.environ["CHROME_BINARY"]
    driver_path = os.getenv("CHROMEDRIVER_PATH")
    service = Service(driver_path) if driver_path else Service()
    driver = webdriver.Chrome(service=service, options=options)
    output = []
    status = "success"
    url = f"https://www.chess.com/member/{name}/games"
    try:
        driver.set_page_load_timeout(60)
        wait = WebDriverWait(driver, 30)
        for index in range(10):
            driver.get(url)
            rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, ROWS)))
            if index >= len(rows):
                break
            link = rows[index].find_element(By.CLASS_NAME, "archived-games-background-link")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", link)
            link.click()

            def share_button(browser):
                for xpath in SHARE_BUTTONS:
                    for element in browser.find_elements(By.XPATH, xpath):
                        if element.is_displayed() and element.is_enabled():
                            return element
                return False

            wait.until(share_button).click()
            wait.until(EC.element_to_be_clickable((By.ID, "tab-pgn"))).click()
            pgn = wait.until(lambda browser: browser.find_element(By.NAME, "pgn").get_attribute("value"))
            game = chess.pgn.read_game(io.StringIO(pgn))
            if game is None or game.errors:
                raise ValueError("Chess.com returned an invalid PGN")
            if cutoff and datetime.datetime.strptime(game.headers["Date"], "%Y.%m.%d").date() <= cutoff:
                status = "old data"
                break
            timestamps = wait.until(EC.element_to_be_clickable((By.ID, "tab-pgn-timestamps")))
            timestamps.click()
            timed = wait.until(lambda browser: (
                value if (value := browser.find_element(By.NAME, "pgn").get_attribute("value"))
                and "%timestamp" in value else False
            ))
            output.append(pgn + "\n ***TimeStamp*** \n" + timed + "\n ***Space*** \n")
        result = "".join(output)
        PGN_DATA_DIR.mkdir(parents=True, exist_ok=True)
        path = PGN_DATA_DIR / f"pgn_data_{datetime.date.today()}_{name}.txt"
        path.write_text(result, encoding="utf-8")
        return status, result
    finally:
        # Includes failed navigation, selector timeouts, and date-cutoff exits.
        driver.quit()


if __name__ == "__main__":
    for username in read_people():
        status, _ = scrapChessData(username)
        print(username, status)
