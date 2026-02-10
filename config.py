import os

# Configuration
EXCEL_FILE_PATH = "schedule.xlsx" # Default local file
SHEET_NAME = "Sheet1" # Update if known

# URL to download the schedule from (optional)
# Using the viewer link directly as download is blocked
SCHEDULE_URL = "https://mailuc-my.sharepoint.com/:x:/g/personal/rhodusla_ucmail_uc_edu/IQDF0zkPUM6KR4Kcez4MPmIxAUSPnTUH4s_D4wUqBxCLQUs"

# Color criteria - OpenPyXL uses aRGB or RGB
# Common "Blue" hex codes. This might need tuning based on the actual file.
# Example: "FF00B0F0" (light blue), "FF0000FF" (blue), "FF4472C4" (accent blue)
TARGET_COLOR_HEXES = ["FF00B0F0", "00B0F0", "FF4472C4", "4472C4", "FF8EA9DB", "8EA9DB"]

# Calendar
CALENDAR_ID = "primary"
EVENT_TITLE = "Focus Session"
EVENT_DURATION_MINUTES = 60 # Default duration if not specified in sheet

# OAuth
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
SCOPES = ['https://www.googleapis.com/auth/calendar']
