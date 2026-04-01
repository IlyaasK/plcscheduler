<<<<<<< HEAD
import requests, pandas, ics, re, datetime

def to24h (time):
    h, m = time.split(":")
    if int(h) < 10:
        h = int(h)
        h+= 12
        h = str(h)
    return f"{h}:{m}:00"

file_download = requests.get("https://mailuc-my.sharepoint.com/:x:/g/personal/rhodusla_ucmail_uc_edu/IQDF0zkPUM6KR4Kcez4MPmIxAQw8SoP576ok5a6k9K_lxuQ?rtime=AiotdL-F3kg&download=1")

physics_classes = {"phys1": [1051, 2001, 2005],
                   "phys2": [1052, 2002, 2006, 2076],
                   "phys3": [3002]}

phys1_calendar = ics.Calendar()
phys2_calendar = ics.Calendar()
phys3_calendar = ics.Calendar()


with open("plcschedule.xlsx", "wb") as file:
    file.write(file_download.content)

data_frame = pandas.read_excel("plcschedule.xlsx", header=None)
schedule = data_frame.iloc[4:22, 1:6]
#print(repr(data_frame.iloc[7, 1]))
date_cell =data_frame.iloc[0, 0]
monday = datetime.datetime.today() + timedelta(days=1) #since running this on sundays

for index, row in schedule.iterrows():
    for cell in row:
        if pandas.notna(cell):
            times = re.findall(r'\d{1,2}:\d{2}', str(cell)) # times
            subjects = re.findall(r'\d{4}', str(cell)) # phys subjects
            title = re.split(r'\d{1,2}:\d{2}', cell)[0].strip() #title
            start_time = to24h(times[0]) 
            end_time = to24h(times[-1])

            session = ics.Event(name = title, location = "Physics Learning Center, Geo-Phys 307", geo=(39.133408839558655, -84.51841831612158), begin = date + " " + start_time, end = date + " " + end_time)
            #figure out how to make sure of correct date using first cell and incrementing with dat of week
            for subject in physics_classes["phys1"]:
                if subject in subjects:
                    phys1_calendar.events.add(session)
                    break
            for s in physics_classes["phys2"]:
                if s in subjects:
                    phys2_calendar.events.add(session)
                    break
            if "3002" in subjects:
                phys3_calendar.events.add(session)

with open('phys1.ics', 'w') as f:
    f.writelines(phys1_calendar.serialize_iter())
with open('phys2.ics', 'w') as f:
    f.writelines(phys2_calendar.serialize_iter())
with open('phys3.ics', 'w') as f:
    f.writelines(phys3_calendar.serialize_iter())

#figure out how to deploy this





=======
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
>>>>>>> bca4c5fbff787c4c7137a8f97bb6b62ab47ab828
