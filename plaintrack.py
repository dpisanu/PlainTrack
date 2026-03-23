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
            duration = (end - start).total_seconds() / 3600.0
            return max(0, duration)
        except Exception:
            return 0.0

    def run_pre_checks(self):
        """Prüft die Infrastruktur und Pfade"""
        print(f"\n--- 1. Initialisierung Arbeitszeit-Report {self.month:02d}/{self.year} ---")
        checks = [
            (f"Root-Verzeichnis", os.path.exists(self.base_path)),
            ("Config-Verzeichnis", os.path.exists(self.config_path)),
            ("Monats-Basisordner", os.path.exists(os.path.join(self.base_path, "months"))),
            (f"Daten für Monat {self.month:02d}", os.path.exists(self.months_path))
        ]
        for msg, result in checks:
            self.log_step(f"Prüfe {msg}...", result)
            if not result:
                self.errors.append(f"Infrastruktur: {msg} nicht gefunden.")
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
        # Wochentage
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
        
        try:
            raw_files = [f for f in os.listdir(self.months_path) if f.endswith(".txt")]
        except Exception:
            self.errors.append("Monatsordner konnte nicht gelesen werden.")
            self.check_and_exit_if_failed("Dateizugriff")
            return

        def get_day_num(filename):
            try: return int(filename.replace(".txt", ""))
            except ValueError: return 999
        # Sortierung vorbereiten und auf Bereich prüfen
        for filename in sorted(raw_files, key=get_day_num):
            day_part = filename.replace(".txt", "")
            try:
                day_val = int(day_part)
                # REGEL: Muss zwischen 1 und Max-Tage des Monats liegen
                if day_val < 1 or day_val > days_in_month:
                    self.log_step(f"Datei {filename.ljust(10)} : UNGÜLTIGER TAG", False)
                    self.errors.append(f"Datei {filename}: Tag existiert nicht.")
                    continue
            except ValueError:
                self.log_step(f"Datei {filename.ljust(10)} : KEINE ZAHL", False)
                self.errors.append(f"Datei {filename}: Name ungültig.")
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
            weekday = curr_date.strftime("%A")
            file_path = os.path.join(self.months_path, f"{d}.txt")
            
            is_workday = weekday in self.config['working_days']
            is_holiday = date_str in self.config['holidays']
            is_closing = date_str in self.config['closing_days']
            
            t_soll_basis = self.config['daily_target'] if (is_workday and not is_holiday and not is_closing) else 0.0
            if t_soll_basis > 0:
                self.results["count_soll_tage"] += 1
            
            t_haben = 0.0
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f if l.strip()]
                
                if "Krank" in lines:
                    self.results["count_krank_tage"] += 1
                    t_soll_basis = 0.0 
                elif "Urlaub" in lines or "Sonderurlaub" in lines:
                    self.results["count_urlaub_tage"] += 1
                    t_soll_basis = 0.0 
                elif "GLZ" in lines:
                    t_haben -= self.config['daily_target']
                    self.results["glz_stunden"] += self.config['daily_target']
                else:
                    day_worked = False
                    for line in lines:
                        if re.match(r'^\d{2}:\d{2}', line):
                            dur = self._parse_duration(line)
                            if "Pause" in line: 
                                self.results["pausenstunden"] += dur
                            else:
                                t_haben += dur
                                self.results["arbeitsstunden_brutto"] += dur
                                if dur > 0: day_worked = True
                    if day_worked:
                        self.results["count_arbeit_tage"] += 1

            self.results["monats_soll"] += t_soll_basis
            self.results["monats_haben"] += t_haben

        self.log_step("Monatsberechnung & Statistik abgeschlossen")

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
            print("-" * 60)
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

if __name__ == "__main__":
    main()