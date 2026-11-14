"""Optional helper: write the currently visible club members to the local roster."""

import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import PEOPLE_FILE


def collect_members():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    if os.getenv('CHROME_BINARY'):
        options.binary_location = os.environ['CHROME_BINARY']
    driver_path = os.getenv('CHROMEDRIVER_PATH')
    driver = webdriver.Chrome(service=Service(driver_path) if driver_path else Service(), options=options)
    try:
        driver.get('https://www.chess.com/clubs/members/bau-chess-club-1')
        members = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located(
            (By.CLASS_NAME, 'clubs-members-list-username-text')
        ))
        names = list(dict.fromkeys(member.text.strip() for member in members if member.text.strip()))
        PEOPLE_FILE.parent.mkdir(parents=True, exist_ok=True)
        PEOPLE_FILE.write_text('\n'.join(names) + '\n')
        return len(names)
    finally:
        driver.quit()


if __name__ == '__main__':
    print(f'Wrote {collect_members()} visible members to {PEOPLE_FILE}')
