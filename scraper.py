# ================================
# Train punctuality scraper - GitHub Actions version
# Runs once per workflow, appends to single CSV
# ================================

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import os

# ----------------
# 0. CONFIG
# ----------------
URL = "https://live.bdz.bg/bg/sofia/arrivals"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# CSV file in repo (single file)
FILE_PATH = "train_punctuality_all.csv"

# ----------------
# 1. SCRAPER FUNCTION
# ----------------
def scrape_trains():
    try:
        response = requests.get(URL, headers=HEADERS)
        response.raise_for_status()
        print(f"[{datetime.utcnow()}] Status code: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.find_all("div", class_="row")
        print(f"[{datetime.utcnow()}] Rows found:", len(rows))

        data = []

        for row in rows:
            train_span = row.find("span", string=re.compile(r"\d+"))
            if not train_span:
                continue
            train = train_span.get_text(strip=True)

            delay_div = row.find("div", class_="col-12 col-lg-3")
            delay_text = delay_div.get_text(strip=True) if delay_div else ""
            delay_text = delay_text.replace("мин.", "").replace("+", "").strip()

            if delay_text == "" or delay_text == "-":
                delay = 0
            else:
                try:
                    delay = int(re.findall(r"\d+", delay_text)[0])
                except:
                    delay = 0

            data.append({
                "train": train,
                "delay_min": delay,
                "scraped_at": datetime.utcnow()
            })

        df = pd.DataFrame(data)

        # Remove duplicates in current scrape
        df = df.drop_duplicates(subset=["train"])

        # Append to CSV
        if not os.path.isfile(FILE_PATH):
            df.to_csv(FILE_PATH, index=False)
        else:
            df.to_csv(FILE_PATH, mode="a", index=False, header=False)

        print(f"[{datetime.utcnow()}] Data appended to {FILE_PATH}")
        print(df)

    except Exception as e:
        print(f"[{datetime.utcnow()}] ERROR:", e)

# ----------------
# 2. RUN SCRAPER ONCE
# ----------------
if __name__ == "__main__":
    scrape_trains()
