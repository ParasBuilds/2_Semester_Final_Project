import glob
import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pymongo import MongoClient
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


DEFAULT_PATTERN = "CRIME_REVIEW_FOR_THE_MONTH_OF_*.csv"


def setup_db(uri="mongodb://localhost:27017/", db_name="CrimeDatabase", collection_name="Analytics"):
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        db = client[db_name]
        collection = db[collection_name]
        print("MongoDB connected successfully.")
        return client, collection
    except Exception as exc:
        print(f"Running in Local-only mode: {exc}")
        return None, None


def load_month_alerts(data_dir, pattern=DEFAULT_PATTERN):
    data = {}
    for path in glob.glob(os.path.join(data_dir, pattern)):
        month_key, display_label = extract_month_label(path)
        if not month_key:
            continue

        df = pd.read_csv(path)
        if "Major Heads" not in df.columns:
            continue

        df["Major Heads"] = df["Major Heads"].fillna("").astype(str).str.strip()
        df = df[df["Major Heads"] != ""]

        prev_series = pd.to_numeric(df.get("During the previous month"), errors="coerce").fillna(0)
        curr_series = pd.to_numeric(df.get("During the current month"), errors="coerce").fillna(0)

        grouped = (
            df.assign(prev=prev_series, curr=curr_series)
            .groupby("Major Heads", sort=True)[["prev", "curr"]]
            .sum()
        )

        prev_vals = grouped["prev"].to_numpy(dtype=float)
        curr_vals = grouped["curr"].to_numpy(dtype=float)
        pct_vals = np.zeros_like(prev_vals, dtype=float)
        zero_prev = prev_vals <= 0
        pct_vals[zero_prev] = np.where(curr_vals[zero_prev] > 0, 100.0, 0.0)
        non_zero_prev = ~zero_prev
        pct_vals[non_zero_prev] = (
            (curr_vals[non_zero_prev] - prev_vals[non_zero_prev])
            / prev_vals[non_zero_prev]
        ) * 100.0

        results = []
        for (category, row), pct in zip(grouped.iterrows(), pct_vals, strict=False):
            results.append({
                "category": category,
                "previous": int(row["prev"]),
                "current": int(row["curr"]),
                "pct": float(pct),
            })

        data[month_key] = {
            "label": display_label,
            "rows": results,
        }

    return data


def extract_month_label(path):
    name = os.path.basename(path)
    token = "CRIME_REVIEW_FOR_THE_MONTH_OF_"
    if not name.startswith(token):
        return None, None
    raw = name[len(token):].rsplit(".csv", 1)[0]
    parts = raw.split("_")
    if len(parts) < 2:
        return None, None
    month_name = parts[0].upper()
    year = next((p for p in parts[1:] if p.isdigit() and len(p) == 4), "")
    short = month_name[:3]
    if not year:
        return short, month_name
    return short, f"{month_name} {year}"


def get_sorted_month_items(month_alerts):
    month_order = {
        "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
        "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
    }

    def sort_key(item):
        key, payload = item
        label = payload.get("label", key)
        parts = label.split()
        month_token = parts[0][:3].upper()
        year = 0
        for part in parts[1:]:
            if part.isdigit() and len(part) == 4:
                year = int(part)
                break
        return (year, month_order.get(month_token, 0))

    items = sorted(month_alerts.items(), key=sort_key)
    return [(key, payload.get("label", key)) for key, payload in items]


def get_chart_data(month_alerts=None):
    if not month_alerts:
        months = ["AUG", "SEP", "OCT", "NOV", "DEC", "JAN", "FEB"]
        incidents = np.array([21500, 22100, 23400, 24100, 25600, 26800, 24500])
        return months, incidents

    month_items = get_sorted_month_items(month_alerts)
    months = [key for key, _ in month_items]
    totals = []
    for key, _ in month_items:
        payload = month_alerts.get(key)
        total_curr = sum(row["current"] for row in payload["rows"]) if payload else 0
        totals.append(total_curr)
    return months, np.array(totals, dtype=int)


def get_dashboard_cards(month_alerts, alert_threshold):
    if not month_alerts:
        return [
            ("TOTAL INCIDENTS", "12,842", "+4.2% ↑"),
            ("RESPONSE TIME", "06:42", "-12s ↓"),
            ("ACTIVE CASES", "158", "Stable"),
        ]

    month_items = get_sorted_month_items(month_alerts)
    latest_key = month_items[-1][0]
    prev_key = month_items[-2][0] if len(month_items) > 1 else None

    latest_payload = month_alerts.get(latest_key) or {"rows": []}
    prev_payload = month_alerts.get(prev_key) or {"rows": []}

    latest_prev_total, latest_curr_total, latest_pct = _compute_totals(latest_payload)
    prev_prev_total, prev_curr_total, prev_pct = _compute_totals(prev_payload)

    incidents_value = f"{latest_curr_total:,}"
    incidents_trend = _format_pct_change(latest_pct)

    latest_response = _response_time_seconds(latest_pct)
    prev_response = _response_time_seconds(prev_pct)
    response_value = _format_time(latest_response)
    response_trend = _format_seconds_change(prev_response, latest_response)

    latest_active = _count_active_cases(latest_payload, alert_threshold)
    prev_active = _count_active_cases(prev_payload, alert_threshold)
    active_value = f"{latest_active}"
    active_trend = _format_count_change(prev_active, latest_active)

    return [
        ("TOTAL INCIDENTS", incidents_value, incidents_trend),
        ("RESPONSE TIME", response_value, response_trend),
        ("ACTIVE CASES", active_value, active_trend),
    ]


def _compute_totals(payload):
    total_prev = sum(row.get("previous", 0) for row in payload.get("rows", []))
    total_curr = sum(row.get("current", 0) for row in payload.get("rows", []))
    if total_prev <= 0 and total_curr > 0:
        total_pct = 100.0
    elif total_prev <= 0:
        total_pct = 0.0
    else:
        total_pct = ((total_curr - total_prev) / total_prev) * 100.0
    return total_prev, total_curr, total_pct


def _format_pct_change(pct):
    if pct > 0:
        return f"+{pct:.1f}% ↑"
    if pct < 0:
        return f"{pct:.1f}% ↓"
    return "Stable"


def _response_time_seconds(pct_change):
    baseline = 7 * 60
    delta = int(round(pct_change * 2))
    response = baseline + delta
    return max(4 * 60, min(12 * 60, response))


def _format_time(seconds):
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def _format_seconds_change(prev_seconds, curr_seconds):
    if prev_seconds is None:
        return "Stable"
    delta = curr_seconds - prev_seconds
    if delta > 0:
        return f"+{delta}s ↑"
    if delta < 0:
        return f"{abs(delta)}s ↓"
    return "Stable"


def _count_active_cases(payload, alert_threshold):
    return sum(1 for row in payload.get("rows", []) if row.get("pct", 0) >= alert_threshold)


def _format_count_change(prev_count, curr_count):
    if prev_count is None:
        return "Stable"
    delta = curr_count - prev_count
    if delta > 0:
        return f"+{delta} ↑"
    if delta < 0:
        return f"{delta} ↓"
    return "Stable"


def build_chart_figure(months, incidents, colors):
    fig, ax = plt.subplots(figsize=(10, 4), facecolor=colors["BG_CARD"])
    ax.set_facecolor(colors["BG_CARD"])

    ax.plot(
        months,
        incidents,
        color=colors["ACCENT"],
        linewidth=3,
        marker="o",
        markersize=8,
        markerfacecolor=colors["BG_MAIN"],
    )
    ax.fill_between(months, incidents, color=colors["ACCENT"], alpha=0.1)

    ax.tick_params(colors=colors["TEXT_MAIN"], labelsize=9)
    ax.spines["bottom"].set_color(colors["BORDER"])

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.grid(axis="y", color=colors["BORDER"], linestyle="--", alpha=0.2)

    return fig, ax


def export_report(month_alerts, save_path, alert_threshold):
    doc = SimpleDocTemplate(save_path, pagesize=landscape(A4), rightMargin=24, leftMargin=24)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Crime Review Report", styles["Title"]))
    story.append(Paragraph(datetime.now().strftime("Generated on %Y-%m-%d %H:%M"), styles["Normal"]))
    story.append(Spacer(1, 12))

    month_items = get_sorted_month_items(month_alerts)
    for idx, (month_key, label) in enumerate(month_items):
        payload = month_alerts.get(month_key)
        if not payload:
            continue

        total_prev = sum(row["previous"] for row in payload["rows"])
        total_curr = sum(row["current"] for row in payload["rows"])
        if total_prev <= 0 and total_curr > 0:
            total_pct = 100.0
        elif total_prev <= 0:
            total_pct = 0.0
        else:
            total_pct = ((total_curr - total_prev) / total_prev) * 100.0

        summary = (
            f"Alert: Crime rate is higher this month (+{total_pct:.1f}%)."
            if total_pct >= alert_threshold
            else f"Status: Crime rate is stable this month ({total_pct:.1f}%)."
        )

        story.append(Paragraph(label, styles["Heading2"]))
        story.append(Paragraph(summary, styles["Normal"]))
        story.append(Spacer(1, 8))

        table_data = [["Category", "Prev", "Curr", "% Change", "Status"]]
        for row in payload["rows"]:
            pct = row["pct"]
            status = "ALERT" if pct >= alert_threshold else "Status"
            table_data.append([
                row["category"],
                str(row["previous"]),
                str(row["current"]),
                f"{pct:.1f}%",
                status,
            ])

        table = Table(table_data, colWidths=[320, 60, 60, 80, 70], repeatRows=1)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

        if idx < len(month_items) - 1:
            story.append(PageBreak())

    doc.build(story)
