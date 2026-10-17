import gspread
from google.oauth2.service_account import Credentials

# Scope
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Credentials
creds = Credentials.from_service_account_file("credentials.json", scopes=scope)

# Connect
client = gspread.authorize(creds)

# Open correct sheet
sheet = client.open("Meta Ads Daily Reports").worksheet("Master_Data")

# Test write
sheet.append_row(["Test Date", "Test Client", "Campaign", 10, 1000, 800, 500, 3000])

print("✅ Connected successfully!")