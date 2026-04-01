import requests
import pandas
import re
import datetime
import uuid

# ── ICS generation helpers ───────────────────────────────────────────────────

def format_dt_ics(date: datetime.date, time_str: str) -> str:
    """Return an iCalendar-formatted datetime string (local, no timezone).
    time_str is 'HH:MM:SS'.
    """
    h, m, s = time_str.split(":")
    dt = datetime.datetime(date.year, date.month, date.day, int(h), int(m), int(s))
    return dt.strftime("%Y%m%dT%H%M%S")

def make_ics_event(title: str, location: str, date: datetime.date,
                   start_time: str, end_time: str) -> str:
    """Return the text of a VEVENT block."""
    uid = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dtstart = format_dt_ics(date, start_time)
    dtend   = format_dt_ics(date, end_time)
    # Escape special characters in title
    safe_title = title.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    return (
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{now}\r\n"
        f"DTSTART:{dtstart}\r\n"
        f"DTEND:{dtend}\r\n"
        f"SUMMARY:{safe_title}\r\n"
        f"LOCATION:{location}\r\n"
        "END:VEVENT\r\n"
    )

def make_ics_calendar(events: list[str]) -> str:
    body = "".join(events)
    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//PLC Scheduler//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        + body
        + "END:VCALENDAR\r\n"
    )

# ── time helpers ─────────────────────────────────────────────────────────────

def to24h(time_str: str) -> str:
    """Convert a PLC schedule time (e.g. '1:00') to 24-hour 'HH:MM:SS'.

    Hours 1-9 on the schedule are always PM (afternoon sessions).
    Hours 10+ are left as-is (AM or already correct).
    """
    h, m = time_str.split(":")
    h = int(h)
    if h < 10:
        h += 12
    return f"{h:02d}:{m}:00"


def parse_monday_from_title(title: str) -> datetime.date:
    """Extract the Monday date from the schedule header cell.

    Handles both same-month and cross-month ranges:
      'Week 9:  March 9 - 13'
      'Week 11: March 30 - April 3'
    Returns a datetime.date for the Monday of that week.
    """
    # Try cross-month format first: "Month Day - Month Day"
    match = re.search(
        r'([A-Za-z]+)\s+(\d{1,2})\s*[-\u2013]\s*(?:[A-Za-z]+\s+)?(\d{1,2})',
        title
    )
    if not match:
        raise ValueError(f"Could not parse date range from title: {title!r}")

    month_name = match.group(1)
    start_day  = int(match.group(2))

    today     = datetime.date.today()
    year      = today.year
    month_num = datetime.datetime.strptime(month_name, "%B").month

    monday = datetime.date(year, month_num, start_day)

    # Sanity-check: the range start should be a Monday — nudge if needed.
    if monday.weekday() != 0:
        monday = monday - datetime.timedelta(days=monday.weekday())

    return monday


# ── configuration ─────────────────────────────────────────────────────────────

SCHEDULE_URL = (
    "https://mailuc-my.sharepoint.com/:x:/g/personal/rhodusla_ucmail_uc_edu/"
    "IQDF0zkPUM6KR4Kcez4MPmIxAQw8SoP576ok5a6k9K_lxuQ"
    "?rtime=AiotdL-F3kg&download=1"
)

PHYSICS_CLASSES = {
    "phys1": {1051, 2001, 2005},
    "phys2": {1052, 2002, 2006, 2076},
    "phys3": {3002},
}

LOCATION = "Physics Learning Center, Geo-Phys 307"

# Columns 1-5 in the spreadsheet → Monday(+0) through Friday(+4)
COL_TO_DAY_OFFSET = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4}

# ── download schedule ─────────────────────────────────────────────────────────

print("Downloading PLC schedule…")
resp = requests.get(SCHEDULE_URL, allow_redirects=True)
with open("plcschedule.xlsx", "wb") as fh:
    fh.write(resp.content)
print("Download complete.")

# ── parse spreadsheet ─────────────────────────────────────────────────────────

data_frame = pandas.read_excel("plcschedule.xlsx", header=None)

# Row 0, col 0 contains the title with the week's date range.
title_cell = str(data_frame.iloc[0, 0])
monday = parse_monday_from_title(title_cell)
print(f"Week starts on Monday: {monday.strftime('%A %B %d, %Y')}")

# ── build event lists ─────────────────────────────────────────────────────────

phys1_events: list[str] = []
phys2_events: list[str] = []
phys3_events: list[str] = []

# Session data: rows 4-22 (0-indexed), columns 1-5 (Mon-Fri).
schedule = data_frame.iloc[4:23, 1:6]

for _row_idx, row in schedule.iterrows():
    for col_idx, cell in enumerate(row, start=1):  # col_idx 1-5
        if not pandas.notna(cell):
            continue

        cell_str = str(cell).strip()
        if not cell_str:
            continue

        # Extract all HH:MM time patterns from the cell.
        times = re.findall(r'\d{1,2}:\d{2}', cell_str)
        if len(times) < 2:
            # Cannot create an event without both start and end time.
            continue

        # Extract 4-digit course numbers.
        subjects = {int(s) for s in re.findall(r'\d{4}', cell_str)}

        # Title is everything before the first time token.
        title = re.split(r'\d{1,2}:\d{2}', cell_str)[0].strip().rstrip('&').strip()

        start_time = to24h(times[0])
        end_time   = to24h(times[-1])

        # Map column index to the correct calendar date.
        day_offset = COL_TO_DAY_OFFSET.get(col_idx)
        if day_offset is None:
            continue
        event_date = monday + datetime.timedelta(days=day_offset)

        vevent = make_ics_event(title, LOCATION, event_date, start_time, end_time)

        if subjects & PHYSICS_CLASSES["phys1"]:
            phys1_events.append(vevent)

        if subjects & PHYSICS_CLASSES["phys2"]:
            phys2_events.append(vevent)

        if subjects & PHYSICS_CLASSES["phys3"]:
            phys3_events.append(vevent)

# ── write ICS files ───────────────────────────────────────────────────────────

with open("phys1.ics", "w") as f:
    f.write(make_ics_calendar(phys1_events))

with open("phys2.ics", "w") as f:
    f.write(make_ics_calendar(phys2_events))

with open("phys3.ics", "w") as f:
    f.write(make_ics_calendar(phys3_events))

print(f"Done. Wrote {len(phys1_events)} phys1, {len(phys2_events)} phys2, "
      f"{len(phys3_events)} phys3 events.")
print("Output files: phys1.ics, phys2.ics, phys3.ics")
