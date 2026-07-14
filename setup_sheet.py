"""
Run this once to write the column header row to your Google Sheet.

Usage:
  1. Copy .streamlit/secrets.toml.template → .streamlit/secrets.toml and fill it in.
  2. pip install gspread google-auth
  3. python setup_sheet.py
"""
import toml
import gspread
from google.oauth2 import service_account

secrets = toml.load(".streamlit/secrets.toml")

creds = service_account.Credentials.from_service_account_info(
    secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly",
    ],
)
client = gspread.authorize(creds)

spreadsheet_id = secrets["google_sheets"]["spreadsheet_id"]
worksheet_name = secrets["google_sheets"].get("worksheet", "Submissions")

sh = client.open_by_key(spreadsheet_id)

# Create or clear the worksheet
try:
    ws = sh.worksheet(worksheet_name)
    ws.clear()
    print(f"Cleared existing worksheet: {worksheet_name}")
except gspread.exceptions.WorksheetNotFound:
    ws = sh.add_worksheet(title=worksheet_name, rows=1000, cols=50)
    print(f"Created new worksheet: {worksheet_name}")

HEADERS = [
    "Submission ID",
    "Submitted At",
    "First Name",
    "Last Name",
    "Email",
    "Job Title",
    "Company",
    "Country",
    "LinkedIn URL",
    "GitHub Username",
    "Twitter / X Handle",
    "Website / Blog",
    # Community
    "Community Identity",
    "Data Superhero Profile URL",
    "Streamlit Creator Profile URL",
    "Snowflake Community Username",
    "Years Using Snowflake",
    # Audience reach
    "LinkedIn Followers",
    "Twitter / X Followers",
    "YouTube Subscribers",
    "Newsletter Subscribers",
    "GitHub Stars (Total)",
    "Other Reach Notes",
    # Past involvement
    "Past Snowflake Talks Count",
    "Past Content Summary",
    "Notable Projects / Contributions",
    # Conference
    "Conference Name",
    "Conference Website",
    "Conference Type",
    "Conference Start Date",
    "Conference End Date",
    "Conference City",
    "Conference Country",
    "Conference Format",
    # Talk
    "Talk Title",
    "Session Type",
    "Talk Abstract",
    "Snowflake Topics",
    "Acceptance Status",
    # Support
    "Support Types Requested",
    "Estimated Travel Cost (USD)",
    "Traveling From",
    "Additional Notes",
]

ws.append_row(HEADERS, value_input_option="RAW")
print(f"Headers written to sheet '{worksheet_name}' in spreadsheet {spreadsheet_id}")
print("Done! Share the spreadsheet URL with the team.")
