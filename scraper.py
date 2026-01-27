import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ----------------
# 0. CONFIG
# ----------------
URL = "https://live.bdz.bg/bg/sofia/arrivals"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
SHEET_NAME = "Train Punctuality Data" # Name of your Google Sheet

# ----------------
# 1. GOOGLE SHEETS SETUP
# ----------------
def get_google_sheet():
    # We will load credentials from an Environment Variable for security
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    creds_dict = json.loads(creds_json)
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # Open the sheet
    try:
        sheet = client.open(SHEET_NAME).sheet1
    except gspread.exceptions.SpreadsheetNotFound:
        print("Error: Spreadsheet not found. Please create it and share with the bot email.")
        raise
    return sheet

# ----------------
# 2. SCRAPER FUNCTION
# ----------------
def scrape_and_save():
    try:
        # --- SCRAPING PART (Same as your code) ---
        response = requests.get(URL, headers=HEADERS)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.find_all("div", class_="row")
        
        new_rows = [] # List of lists for Google Sheets

        for row in rows:
            train_span = row.find("span", string=re.compile(r"\d+"))
            if not train_span: continue
            
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
            
            # Timestamp
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            
            # Prepare row: [Train, Delay, Timestamp]
            new_rows.append([train, delay, now])

        print(f"[{datetime.utcnow()}] Found {len(new_rows)} trains.")

        # --- SAVING PART (Google Sheets) ---
        if new_rows:
            sheet = get_google_sheet()
            # Append all rows at once
            sheet.append_rows(new_rows)
            print("Successfully appended to Google Sheet.")
        else:
            print("No data found to append.")

    except Exception as e:
        print(f"ERROR: {e}")
        # Optional: Raise error so Cloud Run knows it failed
        raise e

if __name__ == "__main__":
    scrape_and_save()
