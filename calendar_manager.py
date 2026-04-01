import os.path
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import config

def get_service():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(config.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, config.SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(config.CREDENTIALS_FILE):
                raise FileNotFoundError(f"Missing {config.CREDENTIALS_FILE}. Please download it from Google Cloud Console.")
            flow = InstalledAppFlow.from_client_secrets_file(
                config.CREDENTIALS_FILE, config.SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(config.TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service

def get_busy_slots(service, time_min, time_max):
    """
    Returns a list of (start, end) tuples for busy times.
    """
    body = {
        "timeMin": time_min.isoformat() + 'Z',
        "timeMax": time_max.isoformat() + 'Z',
        "timeZone": 'UTC',
        "items": [{"id": config.CALENDAR_ID}]
    }
    
    events_result = service.freebusy().query(body=body).execute()
    calendars = events_result.get('calendars', {})
    busy_list = calendars.get(config.CALENDAR_ID, {}).get('busy', [])
    
    busy_slots = []
    for item in busy_list:
        start = datetime.datetime.fromisoformat(item['start'].replace('Z', '+00:00'))
        end = datetime.datetime.fromisoformat(item['end'].replace('Z', '+00:00'))
        # Ensure timezone unaware datetimes are handled if comparing (usually best to keep aware)
        busy_slots.append((start, end))
        
    return busy_slots

def create_event(service, start_dt, end_dt, title):
    event = {
        'summary': title,
        'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': 'America/New_York', # Adjust as needed
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': 'America/New_York',
        },
    }

    event = service.events().insert(calendarId=config.CALENDAR_ID, body=event).execute()
    print(f'Event created: {event.get("htmlLink")}')
    return event
