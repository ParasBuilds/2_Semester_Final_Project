import os
from tkinter import filedialog

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter.messagebox as messagebox

import backend

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

BG_MAIN    = "#10141a"
BG_SIDEBAR = "#181c22"
BG_CARD    = "#1c2026"
ACCENT     = "#ffb77d"
ACCENT_BLUE = "#3cd7ff"
TEXT_MAIN  = "#dfe2eb"
TEXT_SUB   = "#c4c6cf"
TEXT_DARK  = "#2f1500"
BORDER     = "#44474e"
HOVER      = "#ffdcc3"
ALERT_THRESHOLD = 30.0


class CrimeDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LUMINANCE - The Ultimate Crime Analysis Dashboard")
        self.geometry("1200x800")
        self.configure(fg_color=BG_MAIN)

        self.client, self.collection = backend.setup_db()

        self.setup_sidebar()
        self.month_alerts = self.load_month_alerts()
        self.setup_main_view()

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=BG_SIDEBAR)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(
            self.sidebar, text="LUMINANCE",
            font=("Space Grotesk", 24, "bold"), text_color=ACCENT
        ).pack(pady=(40, 20), padx=20)

        nav_buttons = [
            ("DASHBOARD", True, None),
            ("CRIME DATA", False, self.open_crime_data_window),
            ("REPORTS",    False, self.open_reports_window),
        ]
        for label, is_active, command in nav_buttons:
            self.create_nav_button(label, is_active, command)

        ctk.CTkLabel(
            self.sidebar, text="SYSTEM: OPERATIONAL",
            font=("Inter", 10), text_color=ACCENT_BLUE
        ).pack(side="bottom", pady=20)

    def create_nav_button(self, text, is_active, command=None):
        btn_color  = ACCENT         if is_active else "transparent"
        text_color = TEXT_DARK      if is_active else TEXT_MAIN

        btn = ctk.CTkButton(
            self.sidebar, text=text,
            fg_color=btn_color, text_color=text_color,
            hover_color=HOVER, font=("Space Grotesk", 12, "bold"),
            height=40, corner_radius=8, command=command
        )
        btn.pack(pady=10, padx=20, fill="x")
        return btn

    def setup_main_view(self):
        self.main_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_container.pack(side="right", fill="both", expand=True, padx=30, pady=20)

        header = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            header, text="Welcome back, Analyst.",
            font=("Space Grotesk", 34, "bold"), text_color=TEXT_MAIN
        ).pack(side="left")

        ctk.CTkButton(
            header, text="EXPORT REPORT",
            fg_color=ACCENT, text_color=TEXT_DARK,
            command=self.export_data, font=("Space Grotesk", 11, "bold")
        ).pack(side="right", padx=10)

        self.grid_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True)
        self.grid_frame.columnconfigure((0, 1, 2), weight=1)

        cards = backend.get_dashboard_cards(self.month_alerts, ALERT_THRESHOLD)
        card_colors = [ACCENT, ACCENT_BLUE, ACCENT]
        for col, ((title, value, trend), color) in enumerate(zip(cards, card_colors, strict=False)):
            self.create_card(row=0, col=col, title=title, value=value, trend=trend, accent=color)

        self.chart_frame = ctk.CTkFrame(self.grid_frame, fg_color=BG_CARD, corner_radius=15)
        self.chart_frame.grid(row=1, column=0, columnspan=3, pady=20, sticky="nsew")
        self.render_chart()

    def create_card(self, row, col, title, value, trend, accent):
        card = ctk.CTkFrame(self.grid_frame, fg_color=BG_CARD, corner_radius=15, height=140)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)

        ctk.CTkLabel(card, text=title, font=("Space Grotesk", 10, "bold"), text_color=TEXT_SUB ).pack(pady=(20, 0), padx=20, anchor="w")
        ctk.CTkLabel(card, text=value, font=("Space Grotesk", 32, "bold"), text_color=TEXT_MAIN).pack(padx=20, anchor="w")
        ctk.CTkLabel(card, text=trend, font=("Inter", 12),                 text_color=accent   ).pack(padx=20, anchor="w")

    def render_chart(self):
        months, incidents = backend.get_chart_data(self.month_alerts)
        self.chart_months = months

        colors = {
            "BG_MAIN": BG_MAIN,
            "BG_CARD": BG_CARD,
            "ACCENT": ACCENT,
            "TEXT_MAIN": TEXT_MAIN,
            "BORDER": BORDER,
        }
        fig, ax = backend.build_chart_figure(months, incidents, colors)
        self.chart_axes = ax

        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.chart_canvas.draw()
        canvas_widget = self.chart_canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=20, pady=20)
        # Trend-only chart; no click interactions.

    def export_data(self):
        if not self.month_alerts:
            messagebox.showwarning("Export Status", "No monthly crime data found.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Save Crime Review Report",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile="crime_review_report.pdf",
        )
        if not save_path:
            return

        backend.export_report(self.month_alerts, save_path, ALERT_THRESHOLD)
        messagebox.showinfo("Export Status", f"PDF report saved to:\n{save_path}")

    def load_month_alerts(self):
        return backend.load_month_alerts(os.getcwd())

    def parse_int(self, value):
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return 0

    def show_month_alerts(self, month_key):
        if month_key not in self.month_alerts:
            messagebox.showinfo("Crime Alert", f"No data available for {month_key}.")
            return
        payload = self.month_alerts[month_key]
        title = f"Crime Alerts - {payload['label']}"

        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.configure(fg_color=BG_CARD)
        popup.geometry("720x520")
        popup.transient(self)
        popup.grab_set()
        popup.attributes("-topmost", True)

        header = ctk.CTkLabel(
            popup, text=title,
            font=("Space Grotesk", 20, "bold"), text_color=TEXT_MAIN
        )
        header.pack(pady=(20, 10))

        container = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for row in payload["rows"]:
            pct = row["pct"]
            status = "ALERT" if pct >= ALERT_THRESHOLD else "Status"
            color = "#ff7a7a" if pct >= ALERT_THRESHOLD else TEXT_SUB
            text = (
                f"{row['category']}  |  Prev: {row['previous']}  |  "
                f"Curr: {row['current']}  |  Change: {pct:.1f}%  |  {status}"
            )
            ctk.CTkLabel(
                container, text=text,
                font=("Inter", 16), text_color=color, anchor="w"
            ).pack(fill="x", pady=6)

    def open_crime_data_window(self):
        if not self.month_alerts:
            messagebox.showinfo("Crime Data", "No monthly crime data found.")
            return
        if hasattr(self, "crime_data_window") and self.crime_data_window.winfo_exists():
            self.crime_data_window.lift()
            self.crime_data_window.focus_force()
            return

        window = ctk.CTkToplevel(self)
        window.title("Crime Data Alerts")
        window.configure(fg_color=BG_CARD)
        window.geometry("820x600")
        window.transient(self)
        window.grab_set()
        window.attributes("-topmost", True)
        window.state("zoomed")
        self.crime_data_window = window

        header = ctk.CTkLabel(
            window, text="Crime Data Alerts",
            font=("Space Grotesk", 22, "bold"), text_color=TEXT_MAIN
        )
        header.pack(pady=(20, 10))

        month_items = self.get_sorted_month_items()
        self.alert_month_map = {label: key for key, label in month_items}

        controls = ctk.CTkFrame(window, fg_color="transparent")
        controls.pack(fill="x", padx=20)

        ctk.CTkLabel(
            controls, text="Month",
            font=("Space Grotesk", 12, "bold"), text_color=TEXT_SUB
        ).pack(side="left", padx=(0, 10))

        self.month_selector = ctk.CTkComboBox(
            controls,
            values=[label for _, label in month_items],
            font=("Inter", 14),
            command=self.on_month_select
        )
        self.month_selector.pack(side="left")

        self.alert_list_container = ctk.CTkScrollableFrame(window, fg_color="transparent")
        self.alert_list_container.pack(fill="both", expand=True, padx=20, pady=(15, 20))

        default_label = month_items[-1][1]
        self.month_selector.set(default_label)
        self.update_alert_list(self.alert_month_map[default_label])

    def open_reports_window(self):
        if not self.month_alerts:
            messagebox.showinfo("Reports", "No monthly crime data found.")
            return
        if hasattr(self, "reports_window") and self.reports_window.winfo_exists():
            self.reports_window.lift()
            self.reports_window.focus_force()
            return

        window = ctk.CTkToplevel(self)
        window.title("Detailed Crime Report")
        window.configure(fg_color=BG_CARD)
        window.geometry("920x650")
        window.transient(self)
        window.grab_set()
        window.attributes("-topmost", True)
        window.state("zoomed")
        self.reports_window = window

        header = ctk.CTkLabel(
            window, text="Detailed Crime Report",
            font=("Space Grotesk", 22, "bold"), text_color=TEXT_MAIN
        )
        header.pack(pady=(20, 10))

        month_items = self.get_sorted_month_items()
        self.report_month_map = {label: key for key, label in month_items}

        controls = ctk.CTkFrame(window, fg_color="transparent")
        controls.pack(fill="x", padx=20)

        ctk.CTkLabel(
            controls, text="Month",
            font=("Space Grotesk", 12, "bold"), text_color=TEXT_SUB
        ).pack(side="left", padx=(0, 10))

        self.report_month_selector = ctk.CTkComboBox(
            controls,
            values=[label for _, label in month_items],
            font=("Inter", 14),
            command=self.on_report_month_select
        )
        self.report_month_selector.pack(side="left")

        self.report_list_container = ctk.CTkScrollableFrame(window, fg_color="transparent")
        self.report_list_container.pack(fill="both", expand=True, padx=20, pady=(15, 20))

        default_label = month_items[-1][1]
        self.report_month_selector.set(default_label)
        self.update_report_list(self.report_month_map[default_label])

    def on_month_select(self, selection):
        month_key = self.alert_month_map.get(selection)
        if not month_key:
            return
        self.update_alert_list(month_key)

    def on_report_month_select(self, selection):
        month_key = self.report_month_map.get(selection)
        if not month_key:
            return
        self.update_report_list(month_key)

    def update_alert_list(self, month_key):
        for widget in self.alert_list_container.winfo_children():
            widget.destroy()

        payload = self.month_alerts.get(month_key)
        if not payload:
            ctk.CTkLabel(
                self.alert_list_container,
                text="No data available for this month.",
                font=("Inter", 16), text_color=TEXT_SUB
            ).pack(anchor="w", pady=8)
            return

        sorted_rows = sorted(payload["rows"], key=lambda r: r["pct"], reverse=True)
        top_rows = sorted_rows[:6]

        total_prev = sum(row["previous"] for row in payload["rows"])
        total_curr = sum(row["current"] for row in payload["rows"])
        if total_prev <= 0 and total_curr > 0:
            total_pct = 100.0
        elif total_prev <= 0:
            total_pct = 0.0
        else:
            total_pct = ((total_curr - total_prev) / total_prev) * 100.0

        has_alert = total_pct >= ALERT_THRESHOLD
        summary_text = (
            f"Alert: Crime rate is higher this month (+{total_pct:.1f}%)." if has_alert
            else f"Status: Crime rate is stable this month ({total_pct:.1f}%)."
        )
        summary_color = "#ff7a7a" if has_alert else TEXT_SUB

        ctk.CTkLabel(
            self.alert_list_container, text=summary_text,
            font=("Space Grotesk", 16, "bold"), text_color=summary_color
        ).pack(anchor="w", pady=(0, 10))

        table = ctk.CTkFrame(self.alert_list_container, fg_color="transparent")
        table.pack(fill="x")
        col_widths = [360, 80, 80, 100, 90]
        for col, width in enumerate(col_widths):
            table.grid_columnconfigure(col, minsize=width)

        headings = ["Category", "Prev", "Curr", "% Change", "Status"]
        for col, text in enumerate(headings):
            ctk.CTkLabel(
                table, text=text,
                font=("Space Grotesk", 12, "bold"), text_color=TEXT_SUB
            ).grid(row=0, column=col, sticky="w", padx=6, pady=(0, 8))

        for row_index, row in enumerate(top_rows, start=1):
            pct = row["pct"]
            status = "ALERT" if pct >= ALERT_THRESHOLD else "Status"
            color = "#ff7a7a" if pct >= ALERT_THRESHOLD else TEXT_SUB

            values = [
                row["category"],
                str(row["previous"]),
                str(row["current"]),
                f"{pct:.1f}%",
                status,
            ]
            for col, value in enumerate(values):
                anchor = "w" if col == 0 else "e"
                ctk.CTkLabel(
                    table, text=value,
                    font=("Inter", 14), text_color=color
                ).grid(row=row_index, column=col, sticky=anchor, padx=6, pady=2)

            separator = ctk.CTkFrame(table, fg_color=BORDER, height=1)
            separator.grid(
                row=row_index + 1, column=0, columnspan=5,
                sticky="ew", padx=4, pady=2
            )

    def update_report_list(self, month_key):
        for widget in self.report_list_container.winfo_children():
            widget.destroy()

        payload = self.month_alerts.get(month_key)
        if not payload:
            ctk.CTkLabel(
                self.report_list_container,
                text="No data available for this month.",
                font=("Inter", 16), text_color=TEXT_SUB
            ).pack(anchor="w", pady=8)
            return

        total_prev = sum(row["previous"] for row in payload["rows"])
        total_curr = sum(row["current"] for row in payload["rows"])
        if total_prev <= 0 and total_curr > 0:
            total_pct = 100.0
        elif total_prev <= 0:
            total_pct = 0.0
        else:
            total_pct = ((total_curr - total_prev) / total_prev) * 100.0

        summary_text = (
            f"Alert: Crime rate is higher this month (+{total_pct:.1f}%)."
            if total_pct >= ALERT_THRESHOLD
            else f"Status: Crime rate is stable this month ({total_pct:.1f}%)."
        )
        summary_color = "#ff7a7a" if total_pct >= ALERT_THRESHOLD else TEXT_SUB

        ctk.CTkLabel(
            self.report_list_container, text=summary_text,
            font=("Space Grotesk", 16, "bold"), text_color=summary_color
        ).pack(anchor="w", pady=(0, 10))

        table = ctk.CTkFrame(self.report_list_container, fg_color="transparent")
        table.pack(fill="x")
        col_widths = [360, 80, 80, 100, 90]
        for col, width in enumerate(col_widths):
            table.grid_columnconfigure(col, minsize=width)

        headings = ["Category", "Prev", "Curr", "% Change", "Status"]
        for col, text in enumerate(headings):
            ctk.CTkLabel(
                table, text=text,
                font=("Space Grotesk", 12, "bold"), text_color=TEXT_SUB
            ).grid(row=0, column=col, sticky="w", padx=6, pady=(0, 8))

        for row_index, row in enumerate(payload["rows"], start=1):
            pct = row["pct"]
            status = "ALERT" if pct >= ALERT_THRESHOLD else "Status"
            color = "#ff7a7a" if pct >= ALERT_THRESHOLD else TEXT_SUB

            values = [
                row["category"],
                str(row["previous"]),
                str(row["current"]),
                f"{pct:.1f}%",
                status,
            ]
            for col, value in enumerate(values):
                anchor = "w" if col == 0 else "e"
                ctk.CTkLabel(
                    table, text=value,
                    font=("Inter", 14), text_color=color
                ).grid(row=row_index, column=col, sticky=anchor, padx=6, pady=2)

            separator = ctk.CTkFrame(table, fg_color=BORDER, height=1)
            separator.grid(
                row=row_index + 1, column=0, columnspan=5,
                sticky="ew", padx=4, pady=2
            )

    def get_sorted_month_items(self):
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

        return backend.get_sorted_month_items(self.month_alerts)



if __name__ == "__main__":
    app = CrimeDashboard()
    app.mainloop()