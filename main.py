import datetime
import config
import scraper
import calendar_manager
from dateutil import tz
import requests
import os

def download_file(url, target_path):
    try:
        response = requests.get(url, allow_redirects=True)
        if response.status_code == 200:
            with open(target_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded schedule from {url}")
            return True
        else:
            print(f"Failed to download schedule. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading schedule: {e}")
        return False

def check_conflicts(slot_start, slot_end, busy_slots):
    # slot_start and slot_end should be timezone aware if busy_slots are
    # As excel parser returns naive, we should localize them ideally or assume local time.
    
    # Let's assume the Excel sheet is in local time "America/New_York"
    local_tz = tz.gettz("America/New_York")
    if slot_start.tzinfo is None:
        slot_start = slot_start.replace(tzinfo=local_tz)
    if slot_end.tzinfo is None:
        slot_end = slot_end.replace(tzinfo=local_tz)
        
    for busy_start, busy_end in busy_slots:
        # Check overlap
        # (StartA <= EndB) and (EndA >= StartB)
        if slot_start < busy_end and slot_end > busy_start:
            return True # Conflict
    return False

def main():
    print("Starting PHYS2002 Schedule Check...")
    
    # 1. Scrape Schedule
    print(f"Scraping schedule from {config.SCHEDULE_URL}...")
    potential_slots = scraper.scrape_schedule(config.SCHEDULE_URL)
    if not potential_slots:
        print("No blue slots found or error scraping.")
        return
    
    print(f"Found {len(potential_slots)} potential slots.")

    # 2. Setup Calendar
    try:
        service = calendar_manager.get_service()
    except Exception as e:
        print(f"Failed to authenticate with Google Calendar: {e}")
        return

    # 3. Check Conflicts and Schedule
    # Determine the range for freebusy check (min(start) to max(end))
    if not potential_slots:
        return

    min_time = min(s['start'] for s in potential_slots)
    max_time = max(s['end'] for s in potential_slots)
    
    # Add buffer
    busy_slots = calendar_manager.get_busy_slots(service, min_time, max_time)
    
    count_scheduled = 0
    for slot in potential_slots:
        start = slot['start']
        end = slot['end']
        
        if not check_conflicts(start, end, busy_slots):
            print(f"Scheduling {slot['title']} at {start}...")
            calendar_manager.create_event(service, start, end, slot['title'])
            count_scheduled += 1
        else:
            print(f"Skipping {slot['title']} at {start} due to conflict.")

    print(f"Finished. Scheduled {count_scheduled} sessions.")

if __name__ == "__main__":
    main()
