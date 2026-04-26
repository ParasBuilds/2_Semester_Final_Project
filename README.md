# Luminance: Crime Analysis Dashboard

A sleek desktop dashboard for analyzing monthly crime review data. The app ingests the CSVs in `CSV/`, highlights alert-level category changes, visualizes incident trends, and exports a professional PDF report.

## Highlights
- Interactive CustomTkinter UI with a modern dashboard layout.
- Monthly alert detection based on percentage change thresholds.
- Trend visualization with Matplotlib.
- One-click PDF report generation.
- Optional MongoDB connectivity (falls back to local-only mode).

## Tech Stack
- Python 3.x
- CustomTkinter
- Pandas, NumPy
- Matplotlib
- ReportLab
- PyMongo (optional)

## Project Structure
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
1. Create and activate a virtual environment (recommended).
2. Install dependencies:

```bash
pip install customtkinter matplotlib pandas numpy reportlab pymongo
```

## Run
From the project root:

```bash
python main/app.py
```

## Data Notes
- CSVs are read from the `CSV/` folder.
- Alert threshold is set to 30% (see `ALERT_THRESHOLD` in `main/app.py`).
- If MongoDB is unavailable, the app will continue in local-only mode.

## Exported Reports
Use the **EXPORT REPORT** button to generate a PDF summary of each month, including alert status and per-category deltas.

## Credits
Created for a semester capstone project focused on public safety crime analytics.
