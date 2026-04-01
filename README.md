# PHYS2002 Focus Session Scheduler

This project automates the scheduling of "PHYS2002 Focus Sessions" from a SharePoint Excel schedule to a Google Calendar. It scrapes the specific SharePoint URL for "Focus Session" slots (identifying them by text and color), checks for conflicts in your Google Calendar, and adds non-conflicting events.

## Features

- **Automated Scraping**: Uses Playwright to scrape the live SharePoint Excel viewer, handling dynamic content and floating text boxes.
- **Smart Parsing**: Identifies sessions using Regex for time ranges (e.g., "10am-4pm") and dates.
- **Conflict Detection**: Checks your Google Calendar to ensure new sessions don't overlap with existing events.
- **OAuth2 Authentication**: Securely authenticates with Google Calendar API.

## Setup Guide

### 1. Prerequisites

- Python 3.10+
- A Google Cloud Project with Calendar API enabled.

### 2. Google Calendar Credentials

To allow the script to access your calendar, you need a `credentials.json` file.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., "PHYS2002 Scheduler").
3. Navigate to **APIs & Services > Library**.
4. Search for "Google Calendar API" and enable it.
5. Navigate to **APIs & Services > OAuth consent screen**.
   - Choose **External** (or Internal if you have a Workspace).
   - Fill in the required fields (App name, email).
   - Add your email as a **Test User**.
6. Navigate to **APIs & Services > Credentials**.
   - Click **Create Credentials > OAuth client ID**.
   - Select **Desktop app**.
   - Download the JSON file, rename it to `credentials.json`, and place it in this folder.

**Note**: `credentials.json` is git-ignored for security. Do not commit it.

### 3. Installation

```bash
# Install uv if you haven't
pip install uv

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
playwright install chromium
```

### 4. Running the Script

First run (requires browser authentication):

```bash
source .venv/bin/activate
python3 main.py
```

Follow the link in the terminal to authorize the app. A `token.json` file will be created (also git-ignored).

### 5. Automation

To run this automatically every Monday at 9am:

1. Edit your crontab:
   ```bash
   crontab -e
   ```
2. Add the following line:
   ```bash
   0 9 * * 1 /path/to/plcscheduler/run.sh
   ```

## Configuration

- **SharePoint URL**: Configured in `config.py`.
- **Target Calendar**: Default is 'primary'. Change `CALENDAR_ID` in `config.py` if needed.
