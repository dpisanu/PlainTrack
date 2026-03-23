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
            print("❌ Fehler: Jahr und Monat müssen numerisch sein.")
            sys.exit(1)
            
        self.base_path = base_path
        self.config_path = os.path.join(base_path, "config")
        self.months_path = os.path.join(base_path, "months", f"{self.month:02d}")
        self.errors = []
        self.config = {}
        # Ergebnis-Container
        self.results = {
            "monats_soll": 0.0,
            "monats_haben": 0.0,
            "glz_stunden": 0.0,
            "arbeitsstunden_brutto": 0.0,
            "pausenstunden": 0.0,
            "count_soll_tage": 0,
            "count_arbeit_tage": 0,
            "count_krank_tage": 0,
            "count_urlaub_tage": 0
        }
        self.daily_data = []

    def log_step(self, message, success=True):
        """Gibt eine Zeile im Boot-Sequenz-Stil aus"""
        status = "  [ ✅ ]  " if success else "  [ ❌ ]  "
        # Padding für die Nachricht, damit die Status-Symbole untereinander stehen
        print(f"{status} {message}")

    def check_and_exit_if_failed(self, section_name):
        """Prüft, ob Fehler aufgetreten sind und bricht ggf. ab."""
        if self.errors:
            print(f"\n--- 🛑 ABBRUCH: Fehler in '{section_name}' erkannt ---")
            self.print_summary()
            sys.exit(1)

    def _parse_duration(self, time_range_str):
        try:
            match = re.search(r'(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})', time_range_str)
            if not match: return 0.0
            fmt = "%H:%M"
            start = datetime.strptime(match.group(1), fmt)
            end = datetime.strptime(match.group(2), fmt)
            return max(0, (end - start).total_seconds() / 3600.0)
        except Exception:
            return 0.0

    def run_pre_checks(self):
        """Prüft die Infrastruktur und Pfade"""
        print(f"\n--- 1. Initialisierung Arbeitszeit-Report {self.month:02d}/{self.year} ---")
        checks = [
            ("Root-Verzeichnis", os.path.exists(self.base_path)),
            ("Config-Verzeichnis", os.path.exists(self.config_path)),
            ("Monats-Basisordner", os.path.exists(os.path.join(self.base_path, "months"))),
            (f"Daten für Monat {self.month:02d}", os.path.exists(self.months_path))
        ]
        for msg, result in checks:
            self.log_step(f"Prüfe {msg}...", result)
            if not result:
                self.errors.append(f"Infrastruktur: {msg} nicht gefunden.")
        
        # Prüfung auf existierenden Report (Finding #1)
        report_name = f"report_{self.year}_{self.month:02d}.html"
        self.target_report_path = os.path.join(self.months_path, report_name)
        
        if os.path.exists(self.target_report_path):
            self.log_step(f"Report '{report_name}' existiert bereits!", False)
            self.errors.append(f"Datei existiert bereits: {self.target_report_path}")
            
        self.check_and_exit_if_failed("Initialisierung")

    def _validate_numeric_config(self, filename, min_val=0, max_val=None, is_int=False):
        """Validierungshilfe für numerische Dateien"""
        path = os.path.join(self.config_path, filename)
        if not os.path.exists(path):
            self.log_step(f"{filename.ljust(25)} fehlt", False)
            self.errors.append(f"Config: {filename} fehlt")
            return 0.0
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read().strip().replace(',', '.')
                val = int(raw) if is_int else float(raw)
                if val < min_val or (max_val is not None and val > max_val): raise ValueError
                self.log_step(f"{filename.ljust(25)} validiert ({val})")
                return val
        except:
            self.log_step(f"{filename.ljust(25)} ungültig", False)
            self.errors.append(f"Config: {filename} ungültig")
            return 0.0

    def validate_configs(self):
        """Prüft alle 9 Konfigurationsdateien gemäß Spezifikation"""
        print("\n--- 2. Validierung Konfigurationsdateien ---")
        # Numerische Werte
        self.config['daily_target'] = self._validate_numeric_config(".dailytargethours", min_val=1)
        self.config['daily_limit'] = self._validate_numeric_config(".dailylegallimit", min_val=1, max_val=10)
        self.config['weekly_target'] = self._validate_numeric_config(".weeklytargethours", min_val=1)
        self.config['weekly_limit'] = self._validate_numeric_config(".weeklycompanyhourslimit", min_val=1)
        self.config['vacation'] = self._validate_numeric_config(".vacationdays", min_val=1, is_int=True)
        # Sonderurlaub darf >= 0 sein
        self.config['special_vacation'] = self._validate_numeric_config(".specialvacationdays", min_val=0, is_int=True)

        wd_path = os.path.join(self.config_path, ".workingdays")
        if os.path.exists(wd_path):
            with open(wd_path, "r", encoding="utf-8") as f:
                self.config['working_days'] = [l.strip() for l in f if l.strip()]
                self.log_step(".workingdays               validiert")
        else:
            self.log_step(".workingdays               fehlt", False)
            self.errors.append("Config: .workingdays fehlt")

        for cfg in [(".holidays", "holidays"), (".closingdays", "closing_days")]:
            path = os.path.join(self.config_path, cfg[0])
            self.config[cfg[1]] = [] if cfg[1] == "holidays" else {}
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    for l in f:
                        if '|' in l:
                            dt, val = l.split('|')
                            if cfg[1] == "holidays": self.config[cfg[1]].append(dt.strip())
                            else: self.config[cfg[1]][dt.strip()] = val.strip().replace(',', '.')
                self.log_step(f"{cfg[0].ljust(26)} validiert")
            else:
                self.log_step(f"{cfg[0].ljust(26)} fehlt (optional)")
        self.check_and_exit_if_failed("Konfigurationsdateien")

    def validate_day_files(self):
        """Prüft die inhaltlichen Regeln der Tagesdateien"""
        print(f"\n--- 3. Analyse Tagesdateien ({self.month:02d}/{self.year}) ---")
        # Kalender-Basisdaten ermitteln
        _, days_in_month = calendar.monthrange(self.year, self.month)
        raw_files = [f for f in os.listdir(self.months_path) if f.endswith(".txt")]
        
        def get_day_num(f):
            try: return int(f.replace(".txt", ""))
            except: return 999

        for filename in sorted(raw_files, key=get_day_num):
            day_part = filename.replace(".txt", "")
            try:
                day_val = int(day_part)
                if day_val < 1 or day_val > days_in_month:
                    self.log_step(f"Datei {filename.ljust(10)} : UNGÜLTIGER TAG", False)
                    self.errors.append(f"Datei {filename}: Tag existiert nicht.")
                    continue
            except:
                self.log_step(f"Datei {filename.ljust(10)} : NAME UNGÜLTIG", False)
                self.errors.append(f"Datei {filename}: Name muss Zahl sein.")
                continue

            with open(os.path.join(self.months_path, filename), "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
            
            markers = ["Krank", "Urlaub", "Sonderurlaub", "GLZ"]
            found_m = [l for l in lines if l in markers]
            time_regex = r'^\d{2}:\d{2}'
            work_b = [l for l in lines if re.match(time_regex, l) and "Pause" not in l]
            pause_b = [l for l in lines if re.match(time_regex, l) and "Pause" in l]

            f_err = []
            if len(found_m) > 1: f_err.append("Mehrere Marker")
            if found_m and (work_b or pause_b): f_err.append("Mix Marker/Blöcke")
            if pause_b and not work_b: f_err.append("Nur Pausen")
            
            if not f_err: 
                self.log_step(f"Tag {str(day_val).ljust(2)} ({filename.ljust(6)}) : OK")
            else:
                self.log_step(f"Tag {str(day_val).ljust(2)} : FEHLER ({', '.join(f_err)})", False)
                self.errors.append(f"{filename}: {', '.join(f_err)}")
        self.check_and_exit_if_failed("Tagesdateien")

    def calculate_month(self):
        print(f"\n--- 4. Berechnungs-Engine ---")
        _, days_in_month = calendar.monthrange(self.year, self.month)
        
        for d in range(1, days_in_month + 1):
            curr_date = date(self.year, self.month, d)
            date_str = curr_date.strftime("%d.%m")
            weekday = curr_date.strftime("%a") # Kurzform für Tabelle
            file_path = os.path.join(self.months_path, f"{d}.txt")
            
            is_workday = curr_date.strftime("%A") in self.config['working_days']
            is_holiday = date_str in self.config['holidays']
            is_closing = date_str in self.config['closing_days']
            
            t_soll = self.config['daily_target'] if (is_workday and not is_holiday and not is_closing) else 0.0
            if t_soll > 0: self.results["count_soll_tage"] += 1
            
            t_haben, t_pause, note = 0.0, 0.0, ""
            
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f if l.strip()]
                
                if "Krank" in lines:
                    self.results["count_krank_tage"] += 1
                    t_soll, note = 0.0, "Krank"
                elif "Urlaub" in lines or "Sonderurlaub" in lines:
                    self.results["count_urlaub_tage"] += 1
                    t_soll, note = 0.0, "Urlaub"
                elif "GLZ" in lines:
                    t_haben -= self.config['daily_target']
                    self.results["glz_stunden"] += self.config['daily_target']
                    note = "GLZ"
                else:
                    day_worked = False
                    for line in lines:
                        if re.match(r'^\d{2}:\d{2}', line):
                            dur = self._parse_duration(line)
                            if "Pause" in line: t_pause += dur
                            else:
                                t_haben += dur
                                day_worked = True
                    if day_worked: self.results["count_arbeit_tage"] += 1
            
            self.results["monats_soll"] += t_soll
            self.results["monats_haben"] += t_haben
            self.results["pausenstunden"] += t_pause
            
            self.daily_data.append({
                "datum": date_str, "tag": weekday, "soll": t_soll, 
                "haben": t_haben, "pause": t_pause, "note": note
            })
        self.log_step("Monatsberechnung & Statistik abgeschlossen")

    def generate_html(self):
        delta = self.results['monats_haben'] - self.results['monats_soll']
        delta_color = "#2ecc71" if delta >= 0 else "#e74c3c"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; color: #333; max-width: 1000px; margin: 40px auto; padding: 20px; background-color: #f4f7f6; }}
                .header {{ background: #2c3e50; color: white; padding: 25px; border-radius: 8px 8px 0 0; display: flex; justify-content: space-between; align-items: center; }}
                .container {{ background: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
                .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-bottom: 35px; }}
                .card {{ border: 1px solid #e1e8ed; padding: 20px; border-radius: 10px; }}
                .card h3 {{ margin-top: 0; color: #34495e; border-bottom: 2px solid #f1f3f5; padding-bottom: 12px; }}
                .stat-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 1.05em; }}
                
                /* Tabellen-Fix (Finding #2) */
                table {{ width: 100%; border-collapse: collapse; margin-top: 25px; table-layout: fixed; }}
                th {{ background-color: #f8f9fa; color: #7f8c8d; text-transform: uppercase; font-size: 0.85em; letter-spacing: 1px; padding: 15px 5px; border-bottom: 2px solid #dee2e6; text-align: left; }}
                td {{ padding: 12px 5px; border-bottom: 1px solid #f1f3f5; text-align: left; }}
                
                /* Spaltenbreiten definieren für Bündigkeit */
                .col-date {{ width: 15%; }}
                .col-day  {{ width: 10%; }}
                .col-soll {{ width: 15%; }}
                .col-hab  {{ width: 15%; }}
                .col-pau  {{ width: 15%; }}
                .col-note {{ width: 30%; }}

                .weekend {{ background-color: #fcfcfc; color: #bdc3c7; }}
                .marker-note {{ font-weight: bold; color: #2980b9; }}
                .delta-val {{ font-weight: bold; color: {delta_color}; }}
            </style>
            <title>Arbeitszeit-Report {self.month:02d}/{self.year}</title>
        </head>
        <body>
            <div class="header">
                <h1 style="margin:0">Arbeitszeit-Report</h1>
                <span style="font-size: 1.2em;">{self.month:02d} / {self.year}</span>
            </div>
            <div class="container">
                <div class="grid">
                    <div class="card">
                        <h3>Stunden Übersicht</h3>
                        <div class="stat-row"><span>Soll-Zeit:</span> <span>{self.results['monats_soll']:.2f} h</span></div>
                        <div class="stat-row"><span>Haben-Zeit:</span> <span>{self.results['monats_haben']:.2f} h</span></div>
                        <div class="stat-row" style="margin-top:15px; border-top: 1px solid #eee; padding-top: 10px;">
                            <span><strong>DELTA:</strong></span> <span class="delta-val">{delta:.2f} h</span>
                        </div>
                        <div class="stat-row" style="color: #7f8c8d; font-size: 0.9em;"><span>GLZ genutzt:</span> <span>{self.results['glz_stunden']:.2f} h</span></div>
                        <div class="stat-row" style="color: #7f8c8d; font-size: 0.9em;"><span>Pausen:</span> <span>{self.results['pausenstunden']:.2f} h</span></div>
                    </div>
                    <div class="card">
                        <h3>Tagesübersicht</h3>
                        <div class="stat-row"><span>Arbeitstage Soll:</span> <span>{self.results['count_soll_tage']}</span></div>
                        <div class="stat-row"><span>Arbeitstage Ist:</span> <span>{self.results['count_arbeit_tage']}</span></div>
                        <div class="stat-row"><span>Krank:</span> <span>{self.results['count_krank_tage']}</span></div>
                        <div class="stat-row"><span>Urlaub gesamt:</span> <span>{self.results['count_urlaub_tage']}</span></div>
                    </div>
                </div>

                <h3>Detail-Protokoll</h3>
                <table>
                    <thead>
                        <tr>
                            <th class="col-date">Datum</th>
                            <th class="col-day">Tag</th>
                            <th class="col-soll">Soll (h)</th>
                            <th class="col-hab">Haben (h)</th>
                            <th class="col-pau">Pause (h)</th>
                            <th class="col-note">Anmerkung</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        for day in self.daily_data:
            cls = "weekend" if day['tag'] in ['Sa', 'So'] else ""
            html_content += f"""
                <tr class="{cls}">
                    <td>{day['datum']}</td><td>{day['tag']}</td>
                    <td>{day['soll']:.2f}</td><td>{day['haben']:.2f}</td>
                    <td>{day['pause']:.2f}</td><td class="marker-note">{day['note']}</td>
                </tr>"""
        
        html_content += """
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        with open(self.target_report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        self.log_step(f"HTML-Report generiert: {self.target_report_path}")

    def print_summary(self):
        print("\n" + "="*60)
        if self.errors:
            print(f"  ZUSAMMENFASSUNG: {len(self.errors)} FEHLER GEFUNDEN ❌")
            for err in self.errors: print(f"  -> {err}")
        else:
            print(f"  ERGEBNISSE FÜR {self.month:02d}/{self.year} ✅\n")
            print(" Stunden Übersicht:")
            print("-" * 60)
            print(f"  SOLL-Arbeitszeit:    {self.results['monats_soll']:8.2f} h")
            print(f"  HABEN-Arbeitszeit:   {self.results['monats_haben']:8.2f} h")
            print(f"  DELTA:               {(self.results['monats_haben'] - self.results['monats_soll']):8.2f} h")
            print("-" * 60)
            print(f"  Genutzte GLZ:        {self.results['glz_stunden']:8.2f} h")
            print(f"  Pausen gesamt:       {self.results['pausenstunden']:8.2f} h")
            print("-" * 60 + "\n")
            print(" Tagesübersicht:")
            print("-" * 60)
            print(f"  Zu arbeitende Tage:  {self.results['count_soll_tage']:4}")
            print(f"  Gearbeitete Tage:    {self.results['count_arbeit_tage']:4}")
            print(f"  Krankheitstage:      {self.results['count_krank_tage']:4}")
            print(f"  Urlaubstage ges.:    {self.results['count_urlaub_tage']:4}")
        print("="*60 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Arbeitszeit-Auswertungstool v1")
    parser.add_argument("--path", required=True, help="Pfad zum Jahresordner")
    parser.add_argument("--year", required=True, help="Das Jahr")
    parser.add_argument("--month", required=True, help="Der Monat (1-12)")
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