import os
import argparse
import re
from datetime import datetime, date
import calendar

class TimeTrackerReport:
    def __init__(self, base_path, year, month):
        self.base_path = base_path
        self.year = year
        self.month = month
        self.config_path = os.path.join(base_path, "config")
        self.months_path = os.path.join(base_path, "months", f"{month:02d}")
        self.errors = []
        self.warnings = []
        self.config = {}

    def run_pre_checks(self):
        """Prüft die Existenz der Ordnerstruktur"""
        if not os.path.exists(self.base_path):
            self.fail(f"Year-Pfad existiert nicht: {self.base_path}")
        if not os.path.exists(self.config_path):
            self.fail(f"Config-Ordner fehlt: {self.config_path}")
        if not os.path.exists(os.path.dirname(self.months_path)):
            self.fail(f"Ordner 'months' fehlt im Verzeichnis.")
        if not os.path.exists(self.months_path):
            self.fail(f"Keine Daten für Monat {self.month} gefunden: {self.months_path}")

    def validate_configs(self):
        """Validiert die Inhalte der .config Dateien"""
        # Beispiel: .dailytargethours
        target_path = os.path.join(self.config_path, ".dailytargethours")
        if not os.path.exists(target_path):
            self.fail(".dailytargethours fehlt")
        
        with open(target_path, "r") as f:
            val = f.read().strip().replace(',', '.')
            try:
                hours = float(val)
                if hours < 1: raise ValueError()
                self.config['daily_target'] = hours
            except ValueError:
                self.fail(".dailytargethours muss eine Zahl >= 1 sein.")

        # .workingdays einlesen
        working_days_path = os.path.join(self.config_path, ".workingdays")
        if not os.path.exists(working_days_path):
            self.fail(".workingdays fehlt")
        
        with open(working_days_path, "r") as f:
            days = [line.strip() for line in f if line.strip()]
            if not days: self.fail(".workingdays ist leer")
            if len(days) != len(set(days)): self.fail("Doppelte Einträge in .workingdays")
            self.config['working_days'] = days

    def validate_day_files(self):
        """Prüft die Regeln für jede Tagesdatei im Monatsordner"""
        files = [f for f in os.listdir(self.months_path) if f.endswith(".txt")]
        if not files:
            self.fail(f"Keine Tagesdateien (.txt) in {self.months_path} gefunden.")

        for filename in files:
            day_num = filename.replace(".txt", "")
            if not day_num.isdigit() or not (1 <= int(day_num) <= 31):
                self.errors.append(f"Ungültiger Dateiname: {filename}")
                continue
            
            self.check_file_content(os.path.join(self.months_path, filename), filename)

    def check_file_content(self, file_path, label):
        """Inhaltliche Prüfung gemäß Spezifikation"""
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        
        markers = ["Krank", "Urlaub", "Sonderurlaub", "GLZ"]
        found_markers = [l for l in lines if l in markers]
        work_blocks = [l for l in lines if l.startswith("-") and "Pause" not in l]
        pause_blocks = [l for l in lines if l.startswith("-") and "Pause" in l]

        # Regel: Mehrere Marker nicht erlaubt
        if len(found_markers) > 1:
            self.errors.append(f"{label}: Mehrere Tageszustände gefunden.")

        # Regel: Marker und Blöcke nicht kombinierbar
        if found_markers and (work_blocks or pause_blocks):
            self.errors.append(f"{label}: Tageszustand darf nicht mit Arbeits-/Pausenblöcken kombiniert werden.")

        # Regel: Nur Pausenblöcke ohne Arbeit nicht erlaubt
        if pause_blocks and not work_blocks and not found_markers:
            self.errors.append(f"{label}: Enthält nur Pausen, keine Arbeitsblöcke.")

        # Zeitüberlappung & Doppelte Zeitblöcke (v1 Happy Path check)
        times = []
        for b in work_blocks + pause_blocks:
            # Extrahiere Zeiten wie "08:30 - 12:00"
            match = re.search(r'(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})', b)
            if match:
                times.append(match.groups())
        
        if len(times) != len(set(times)):
            self.errors.append(f"{label}: Mehrfacheintrag desselben Zeitblocks.")

    def fail(self, msg):
        print(f"CRITICAL ERROR: {msg}")
        exit(1)

    def report_results(self):
        print(f"--- Validierung für {self.month:02d}/{self.year} abgeschlossen ---")
        if not self.errors:
            print("✅ Alle Regeln für v1 eingehalten.")
        else:
            print(f"❌ {len(self.errors)} Fehler gefunden:")
            for err in self.errors:
                print(f"  - {err}")

def main():
    parser = argparse.ArgumentParser(description="Arbeitszeit-Auswertungstool v1")
    parser.add_argument("--path", required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)
    args = parser.parse_args()

    tracker = TimeTrackerReport(args.path, args.year, args.month)
    tracker.run_pre_checks()
    tracker.validate_configs()
    tracker.validate_day_files()
    tracker.report_results()

if __name__ == "__main__":
    main()