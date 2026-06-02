import os
import argparse
import sys
import calendar
import re
from datetime import datetime, date


class TimeTrackerReport:
    def __init__(self, base_path, year, month):
        try:
            self.year = int(year)
            self.month = int(month)
        except ValueError:
            print("❌ Error: The year and month must be entered as numbers.")
            sys.exit(1)

        if self.month < 1 or self.month > 12:
            print("❌ Error: The month must be between 1 and 12.")
            sys.exit(1)

        self.base_path = base_path
        self.config_path = os.path.join(base_path, "config")
        self.months_path = os.path.join(base_path, "months", f"{self.month:02d}")
        self.errors = []
        self.config = {}

        # Ergebnis-Container
        self.results = {
            "monthly_target": 0.0,
            "monthly_have": 0.0,
            "flx_hours": 0.0,
            "gross_working_hours": 0.0,
            "breakhours": 0.0,
            "count_target_days": 0,
            "count_work_days": 0,
            "count_of_sick_days": 0,
            "count_vacation_days": 0,
        }
        self.daily_data = []
        self.report_name = f"report_{self.year}_{self.month:02d}.html"
        self.target_report_path = os.path.join(self.months_path, self.report_name)

    def log_step(self, message, success=True):
        """Outputs a line in boot sequence style."""
        status = "  [ ✅ ]  " if success else "  [ ❌ ]  "
        print(f"{status} {message}")

    def check_and_exit_if_failed(self, section_name):
        """Checks for errors and terminates the process if any are found."""
        if self.errors:
            print(f"\n--- 🛑 ABORT: Error in '{section_name}' recognized ---")
            self.print_summary()
            sys.exit(1)

    def _parse_duration(self, time_range_str):
        try:
            match = re.search(r"(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})", time_range_str)
            if not match:
                return 0.0
            fmt = "%H:%M"
            start = datetime.strptime(match.group(1), fmt)
            end = datetime.strptime(match.group(2), fmt)
            return max(0, (end - start).total_seconds() / 3600.0)
        except Exception:
            return 0.0

    def _parse_time_range(self, line):
        """Returns the start, end, and duration for a time line."""
        match = re.search(r"(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})", line)
        if not match:
            return None, None, 0.0
        start_str, end_str = match.group(1), match.group(2)
        return start_str, end_str, self._parse_duration(line)

    def run_pre_checks(self):
        """Checks the infrastructure and paths."""
        print(f"\n--- 1. Initialization of the Work Time Report {self.month:02d}/{self.year} ---")
        checks = [
            ("Root-Folder", os.path.exists(self.base_path)),
            ("Config-Folder", os.path.exists(self.config_path)),
            ("Month-Basefolder", os.path.exists(os.path.join(self.base_path, "months"))),
            (f"Datasets for Month {self.month:02d}", os.path.exists(self.months_path)),
        ]
        for msg, result in checks:
            self.log_step(f"Checking {msg}...", result)
            if not result:
                self.errors.append(f"Infrastructure: {msg} not found.")

        # Check for existing reports
        if os.path.exists(self.target_report_path):
            self.log_step(f"Report '{self.report_name}' exists already!", False)
            self.errors.append(f"File exists already: {self.target_report_path}")

        self.check_and_exit_if_failed("Initialization")

    def _validate_numeric_config(self, filename, min_val=0, max_val=None, is_int=False):
        """Validation tool for numerical files."""
        path = os.path.join(self.config_path, filename)
        if not os.path.exists(path):
            self.log_step(f"{filename.ljust(25)} missing", False)
            self.errors.append(f"Config: {filename} missing")
            return 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read().strip().replace(",", ".")
                val = int(raw) if is_int else float(raw)
                if val < min_val or (max_val is not None and val > max_val):
                    raise ValueError
                self.log_step(f"{filename.ljust(25)} validated ({val})")
                return val
        except Exception:
            self.log_step(f"{filename.ljust(25)} invalid", False)
            self.errors.append(f"Config: {filename} invalid")
            return 0

    def validate_configs(self):
        """Checks all configuration files according to the Reporter CLI flow."""
        print("\n--- 2. Validation of configuration files ---")

        # Numerical values
        self.config["daily_target"] = self._validate_numeric_config(".dailytargethours", min_val=1)
        self.config["daily_limit"] = self._validate_numeric_config(".dailylegallimit", min_val=1, max_val=10)
        self.config["weekly_target"] = self._validate_numeric_config(".weeklytargethours", min_val=1)
        self.config["weekly_limit"] = self._validate_numeric_config(".weeklycompanyhourslimit", min_val=1)
        self.config["vacation"] = self._validate_numeric_config(".vacationdays", min_val=1, is_int=True)
        # Special leave may be >= 0
        self.config["special_vacation"] = self._validate_numeric_config(".specialvacationdays", min_val=0, is_int=True)

        wd_path = os.path.join(self.config_path, ".workingdays")
        if os.path.exists(wd_path):
            with open(wd_path, "r", encoding="utf-8") as f:
                self.config["working_days"] = [l.strip() for l in f if l.strip()]
                self.log_step(".workingdays               validated")
        else:
            self.log_step(".workingdays               missing", False)
            self.errors.append("Config: .workingdays missing")

        # Optional: Holidays and closing days are included in the extended HTML report
        # saved as a map so that annotations can be displayed.
        self.config["holidays"] = {}
        holidays_path = os.path.join(self.config_path, ".holidays")
        if os.path.exists(holidays_path):
            with open(holidays_path, "r", encoding="utf-8") as f:
                for line in f:
                    raw = line.strip()
                    if not raw:
                        continue
                    if "|" in raw:
                        dt, label = raw.split("|", 1)
                        self.config["holidays"][dt.strip()] = label.strip() or "Holiday"
                    else:
                        self.config["holidays"][raw] = "Holiday"
            self.log_step(f"{'.holidays'.ljust(26)} validated")
        else:
            self.log_step(f"{'.holidays'.ljust(26)} missing (optional)")

        self.config["closing_days"] = {}
        closing_path = os.path.join(self.config_path, ".closingdays")
        if os.path.exists(closing_path):
            with open(closing_path, "r", encoding="utf-8") as f:
                for line in f:
                    raw = line.strip()
                    if not raw:
                        continue
                    if "|" in raw:
                        dt, label = raw.split("|", 1)
                        # The original reporter_full.py HTML report is shown here
                        # Closing date instead of the raw value from the config.
                        self.config["closing_days"][dt.strip()] = "Closed" if label.strip() else "Closed"
                    else:
                        self.config["closing_days"][raw] = "Closed"
            self.log_step(f"{'.closingdays'.ljust(26)} validated")
        else:
            self.log_step(f"{'.closingdays'.ljust(26)} missing (optional)")

        self.check_and_exit_if_failed("Configuration files")

    def validate_day_files(self):
        """Checks the content rules of the daily files."""
        print(f"\n--- 3. Analyse Tagesdateien ({self.month:02d}/{self.year}) ---")
        _, days_in_month = calendar.monthrange(self.year, self.month)
        raw_files = [f for f in os.listdir(self.months_path) if f.endswith(".txt")]

        def get_day_num(filename):
            try:
                return int(filename.replace(".txt", ""))
            except Exception:
                return 999

        for filename in sorted(raw_files, key=get_day_num):
            day_part = filename.replace(".txt", "")
            try:
                day_val = int(day_part)
                if day_val < 1 or day_val > days_in_month:
                    self.log_step(f"File {filename.ljust(10)} : INVALID DAY", False)
                    self.errors.append(f"File {filename}: Day does not exist.")
                    continue
            except Exception:
                self.log_step(f"File {filename.ljust(10)} : NAME INVALID", False)
                self.errors.append(f"File {filename}: Name must be a number.")
                continue

            with open(os.path.join(self.months_path, filename), "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]

            markers = ["sick", "vacation", "specialleave", "flex"]
            found_m = [l for l in lines if l in markers]
            time_regex = r"^\d{2}:\d{2}"
            work_b = [l for l in lines if re.match(time_regex, l) and "break" not in l]
            break_b = [l for l in lines if re.match(time_regex, l) and "break" in l]

            f_err = []
            if len(found_m) > 1:
                f_err.append("Multiple markers")
            if found_m and (work_b or break_b):
                f_err.append("Mix markers/blocks")
            if break_b and not work_b:
                f_err.append("Only breaks")

            if not f_err:
                self.log_step(f"Day {str(day_val).ljust(2)} ({filename.ljust(6)}) : OK")
            else:
                self.log_step(f"Day {str(day_val).ljust(2)} : ERROR ({', '.join(f_err)})", False)
                self.errors.append(f"{filename}: {', '.join(f_err)}")

        self.check_and_exit_if_failed("Day files")

    def calculate_month(self):
        print("\n--- 4. Calculation-Engine ---")
        _, days_in_month = calendar.monthrange(self.year, self.month)

        for d in range(1, days_in_month + 1):
            curr_date = date(self.year, self.month, d)
            date_str = curr_date.strftime("%d.%m")
            weekday_long = curr_date.strftime("%A")
            file_path = os.path.join(self.months_path, f"{d}.txt")

            is_workday = weekday_long in self.config["working_days"]
            is_holiday = date_str in self.config["holidays"]
            is_closing = date_str in self.config["closing_days"]

            t_target = self.config["daily_target"] if (is_workday and not is_holiday and not is_closing) else 0.0
            if t_target > 0:
                self.results["count_target_days"] += 1

            t_have, t_break, note = 0.0, 0.0, ""
            is_special = False
            is_file = False
            work_blocks, break_blocks = 0, 0
            first_start, last_end = "--:--", "--:--"
            all_starts, all_ends = [], []

            if os.path.exists(file_path):
                is_file = True
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f if l.strip()]

                if "sick" in lines:
                    self.results["count_of_sick_days"] += 1
                    t_target, note = 0.0, "Krank"
                elif "vacation" in lines or "specialleave" in lines:
                    self.results["count_vacation_days"] += 1
                    t_target = 0.0
                    note = "specialleave" if "specialleave" in lines else "vacation"
                elif "flex" in lines:
                    t_have -= self.config["daily_target"]
                    self.results["flx_hours"] += self.config["daily_target"]
                    note = "GLZ"
                else:
                    day_worked = False
                    for line in lines:
                        if re.match(r"^\d{2}:\d{2}", line):
                            start_str, end_str, dur = self._parse_time_range(line)
                            if "Break" in line:
                                t_break += dur
                                break_blocks += 1
                            else:
                                t_have += dur
                                work_blocks += 1
                                if start_str:
                                    all_starts.append(start_str)
                                if end_str:
                                    all_ends.append(end_str)
                                day_worked = True

                    if day_worked:
                        self.results["count_work_days"] += 1
                        if t_target == 0:
                            note, is_special = "Special working hours", True
                        if all_starts:
                            first_start = min(all_starts)
                        if all_ends:
                            last_end = max(all_ends)

            if not note:
                if is_holiday:
                    note = self.config["holidays"].get(date_str, "Holiday")
                elif is_closing:
                    note = self.config["closing_days"].get(date_str, "Closed")

            self.results["monthly_target"] += t_target
            self.results["monthly_have"] += t_have
            self.results["gross_working_hours"] += t_have + t_break
            self.results["breakhours"] += t_break

            self.daily_data.append({
                "date": date_str,
                "day": curr_date.strftime("%a"),
                "should": t_target,
                "have": t_have,
                "break": t_break,
                "note": note,
                "is_special": is_special,
                "is_inactive": (t_target == 0 and not is_file),
                "w_blocks": work_blocks,
                "b_blocks": break_blocks,
                "start": first_start,
                "end": last_end,
            })

        self.log_step("Monthly Calculation & Statistics Completed")

    def generate_html(self):
        print("\n--- 5. HTML-Report Information ---")
        delta = self.results["monthly_have"] - self.results["monthly_target"]
        delta_color = "#2ecc71" if delta >= 0 else "#e74c3c"

        html = f"""
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <meta charset="UTF-8">
            <title>Work Hours Report {self.month:02d}/{self.year}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, sans-serif; color: #333; max-width: 1200px; margin: 40px auto; padding: 20px; background-color: #f4f7f6; }}
                .header {{ background: #2c3e50; color: white; padding: 25px; border-radius: 8px 8px 0 0; display: flex; justify-content: space-between; align-items: center; }}
                .container {{ background: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
                .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-bottom: 35px; }}
                .card {{ border: 1px solid #e1e8ed; padding: 20px; border-radius: 10px; }}
                .card h3 {{ margin-top: 0; color: #34495e; border-bottom: 2px solid #f1f3f5; padding-bottom: 12px; margin-bottom: 15px; }}
                .stat-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 1.05em; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 25px; font-size: 0.9em; }}
                th {{ background-color: #f8f9fa; color: #7f8c8d; text-transform: uppercase; font-size: 0.75em; letter-spacing: 1px; padding: 12px 5px; border-bottom: 2px solid #dee2e6; text-align: center; }}
                td {{ padding: 10px 5px; border-bottom: 1px solid #f1f3f5; text-align: center; }}
                .text-left {{ text-align: left; }}
                .inactive-day {{ color: #bdc3c7; font-style: italic; }}
                .marker-note {{ font-weight: bold; color: #2980b9; font-style: normal; }}
                .special-work {{ font-weight: bold; color: #e67e22; border: 1px solid #f39c12; padding: 2px 6px; border-radius: 4px; background-color: #fef5e7; font-style: normal; }}
                .delta-val {{ font-weight: bold; color: {delta_color}; }}
                .have_over {{ color: #27ae60; font-weight: bold; }}
                .have_under {{ color: #e67e22; font-weight: bold; }}
                .block-info {{ color: #95a5a6; font-size: 0.85em; }}
            </style>
        </head>
        <body>
            <div class="header"><h1 style="margin:0">Work Hours Report</h1><span style="font-size: 1.2em;">{self.month:02d} / {self.year}</span></div>
            <div class="container">
                <div class="grid">
                    <div class="card">
                        <h3>Hours Overview</h3>
                        <div class="stat-row"><span>Target time:</span> <span>{self.results['monthly_target']:.2f} h</span></div>
                        <div class="stat-row"><span>Time to have:</span> <span>{self.results['monthly_have']:.2f} h</span></div>
                        <div class="stat-row" style="margin-top:15px; border-top: 1px solid #eee; padding-top: 10px;">
                            <span><strong>DELTA:</strong></span> <span class="delta-val">{delta:.2f} h</span>
                        </div>
                    </div>
                    <div class="card">
                        <h3>Day Overview</h3>
                        <div class="stat-row"><span>Target number of workdays:</span> <span>{self.results['count_target_days']}</span></div>
                        <div class="stat-row"><span>Actual workdays:</span> <span>{self.results['count_work_days']}</span></div>
                        <div class="stat-row"><span>Sick / Vacation:</span> <span>{self.results['count_of_sick_days']} / {self.results['count_vacation_days']}</span></div>
                    </div>
                </div>
                <h3>Detail-Protocol</h3>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 80px;">DATE</th><th style="width: 50px;">TAG</th>
                            <th>SHOULD (H)</th><th>HAVE (H)</th><th>BREAK (H)</th>
                            <th class="block-info">W-BOCKS</th><th class="block-info">B-BLOCKS</th>
                            <th>START</th><th>ENDE</th>
                            <th class="text-left" style="width: 200px;">COMMENT</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for d in self.daily_data:
            row_cls = "inactive-day" if d["is_inactive"] else ""
            hab_cls = "have-over" if d["have"] > d["should"] else ("have_under" if d["have"] < d["should"] and not d["is_inactive"] else "")

            note_html = d["note"]
            if d["is_special"]:
                note_html = f'<span class="special-work">{d["note"]}</span>'
            elif d["note"]:
                note_html = f'<span class="marker-note">{d["note"]}</span>'

            html += f"""<tr class="{row_cls}">
                <td>{d['date']}</td><td>{d['day']}</td>
                <td>{d['should']:.2f}</td><td class="{hab_cls}">{d['have']:.2f}</td><td>{d['break']:.2f}</td>
                <td class="block-info">{d['w_blocks'] if d['w_blocks'] > 0 else '-'}</td>
                <td class="block-info">{d['b_blocks'] if d['b_blocks'] > 0 else '-'}</td>
                <td>{d['start']}</td><td>{d['end']}</td>
                <td class="text-left">{note_html}</td>
            </tr>"""

        html += "</tbody></table></div></body></html>"

        try:
            with open(self.target_report_path, "w", encoding="utf-8") as f:
                f.write(html)
            self.log_step(f"File Name: {self.report_name}")
            self.log_step("Status:     SUCCESSFULLY CREATED")
        except Exception as e:
            self.log_step(f"File Name: {self.report_name}")
            self.log_step(f"Status:    ERROR ({e})", False)
            self.errors.append(f"The HTML report could not be generated: {e}")
        print("\n" + "=" * 60 + "\n")

    def print_summary(self):
        print("\n" + "=" * 60)
        if self.errors:
            print(f"  Summary: {len(self.errors)} ERROR FOUND ❌")
            for err in self.errors:
                print(f"  -> {err}")
        else:
            print(f"RESULTS FOR {self.month:02d}/{self.year} ✅\n")
            print(" Hour overviews:")
            print("-" * 60)
            print(f"  Target working hours:    {self.results['monthly_target']:8.2f} h")
            print(f"  Completed Working hours: {self.results['monthly_have']:8.2f} h")
            print(f"  DELTA:                   {(self.results['monthly_have'] - self.results['monthly_target']):8.2f} h")
            print("-" * 60)
            print(f"  Used flex:    {self.results['flx_hours']:8.2f} h")
            print(f"  Total Breaks: {self.results['breakhours']:8.2f} h")
            print("-" * 60 + "\n")
            print(" Daily Overview:")
            print("-" * 60)
            print(f"  Days to be worked:   {self.results['count_target_days']:4}")
            print(f"  Days worked:         {self.results['count_work_days']:4}")
            print(f"  Sick days:           {self.results['count_of_sick_days']:4}")
            print(f"  Total vacation days: {self.results['count_vacation_days']:4}")
        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Work Time Analysis Tool")
    parser.add_argument("--path", required=True, help="Path to the working folder")
    parser.add_argument("--year", required=True, help="Year")
    parser.add_argument("--month", required=True, help="Which month report should be generated (1-12)")
    args = parser.parse_args()

    tracker = TimeTrackerReport(args.path, args.year, args.month)
    tracker.run_pre_checks()
    tracker.validate_configs()
    tracker.validate_day_files()
    tracker.calculate_month()
    tracker.print_summary()
    if not tracker.errors:
        tracker.generate_html()

if __name__ == "__main__":
    main()