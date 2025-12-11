import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
gc = gspread.authorize(creds)

SPREADSHEET_ID = "13c6B7t3Enm9l1JVM1rU0fvUg1Q9p9CGGUJJhxVD5GKk"

sh = gc.open_by_key(SPREADSHEET_ID)
ws = sh.sheet1

data = ws.get_all_records()

df = pd.DataFrame(data)

OUTPUT_FILE = "latest_schedule.csv"

df.to_csv(OUTPUT_FILE, index=False)

print("Saved CSV to:", os.path.abspath(OUTPUT_FILE))
print("Preview:")
print(df.head())
