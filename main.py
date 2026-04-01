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





