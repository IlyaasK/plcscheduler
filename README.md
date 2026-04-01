# PLC Scheduler

Automatically generates `.ics` calendar files from the University of Cincinnati [Physics Learning Center](https://www.artsci.uc.edu/departments/physics/physics-learning-center.html) weekly schedule spreadsheet.

A GitHub Pages site lets students subscribe to their course calendar with a single tap or QR scan.

## 📅 Subscribe

**[ilyaask.github.io/plcscheduler](https://ilyaask.github.io/plcscheduler)**

| Calendar | Courses |
|----------|---------|
| Physics I | PHYS 1051, 2001, 2005 |
| Physics II | PHYS 1052, 2002, 2006, 2076 |
| Physics III | PHYS 3002 |

Calendars update automatically every week. Subscribe once and sessions appear in your calendar app automatically.

## How it works

`main.py` downloads the PLC schedule spreadsheet every Sunday, parses session titles, times, and course numbers from each cell, determines the correct date for each session based on the week's Monday date in the spreadsheet header, and writes three `.ics` files.

The generated files are served via GitHub Pages alongside `index.html`, which provides QR codes and `webcal://` subscribe links.

## Running locally

```bash
pip install requests pandas openpyxl
python main.py
```

## Enabling GitHub Pages

Go to **Settings → Pages**, set the source to the `main` branch at the root `/`, and save. The site will be live at `https://<your-username>.github.io/plcscheduler/`.

> **Note:** The `.ics` files are git-ignored since they are regenerated weekly. To serve them via GitHub Pages you will need a CI job (e.g. GitHub Actions) that runs `main.py` on a schedule and commits the output files.
