# Luminance: Crime Analysis Dashboard

This is my semester capstone project. It is a desktop dashboard that reads monthly crime review CSV files, highlights alert-level changes, shows a trend chart, and lets you export a PDF report.

## What it does
- Clean UI built with CustomTkinter.
- Flags categories with big month-to-month changes.
- Line chart for total incidents over time.
- One-click PDF report export.
- Tries MongoDB if available, but still runs without it.

## Tech stack
- Python 3.x
- CustomTkinter
- Pandas, NumPy
- Matplotlib
- ReportLab

## Folder layout
```
.
├─ CSV/                     # Monthly crime review CSV files
├─ Extra/                   # Reference PDFs
├─ main/                    # Application source
│  ├─ app.py                # UI + user interactions
│  └─ backend.py            # Data processing + reporting
├─ crime_jan_2026_flowchart.png
├─ Crime_Analysis_Project_Explanation.pdf
├─ Capstone Project.pdf
├─ Public_Safety_Crime_Analytics.pdf
└─ README.md
```

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install customtkinter matplotlib pandas numpy reportlab pymongo
```

## Run
From the project root:

```bash
python main/app.py
```

## Notes
- CSVs are read from the CSV folder.
- The alert threshold is 30% (see ALERT_THRESHOLD in main/app.py).
- If MongoDB is not running, the app just uses local files.

## Report export
Use the EXPORT REPORT button to generate a PDF summary for each month.

## Credits
Made for a semester capstone on public safety crime analytics.
