import os
import json
import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# 1. Setup Authentication
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds_json = json.loads(os.environ['GCP_CREDENTIALS'])
creds = Credentials.from_service_account_info(creds_json, scopes=scope)
client = gspread.authorize(creds)

# 2. Configuration
SHEET_ID = 'YOUR_SPREADSHEET_ID_HERE'
sheet = client.open_by_key(SHEET_ID).worksheet("Top_250_Stocks")

def fetch_nse_data():
    # NSE Bhavcopy URL (Commonly used endpoint)
    url = "https://archives.nseindia.com/content/historical/EQUITIES/2026/MAY/cm15MAY2026bhav.csv.zip"
    # Note: Real bots usually calculate the date dynamically.
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    
    # Process CSV (Assuming zip extraction)
    df = pd.read_csv(url, compression='zip')
    
    # 3. Anti-Noise Filtering
    # Remove ETFs, Debt, and non-equity series
    df = df[df['SERIES'] == 'EQ']
    excluded_keywords = ['BEES', 'ETF', 'GOLD', 'LIQUID', 'NETIT']
    df = df[~df['SYMBOL'].str.contains('|'.join(excluded_keywords), case=False)]
    
    # 4. Sort by Volume and pick Top 250
    df_top = df.sort_values(by='TOTTRDQTY', ascending=False).head(250)
    return df_top[['SYMBOL', 'TOTTRDQTY', 'CLOSE']]

def update_sheet():
    data = fetch_nse_data()
    # Prepare data for Google Sheets (List of lists)
    values = [data.columns.values.tolist()] + data.values.tolist()
    
    # Clear and Update
    sheet.clear()
    sheet.update('A1', values)
    
    # Timestamp for tracking
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.update('E1', [[f"Last Updated: {now} (IST)"]])

if __name__ == "__main__":
    update_sheet()