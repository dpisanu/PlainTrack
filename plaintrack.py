import os
import argparse
import re
import sys
from datetime import datetime

class TimeTrackerReport:
    def __init__(self, base_path, year, month):
        self.base_path = base_path
        self.year = int(year)
        self.month = int(month)
        self.config_path = os.path.join(base_path, "config")
        self.months_path = os.path.join(base_path, "months", f"{self.month:02d}")
        self.errors = []
        self.config = {}

    def log_step(self, message, success=True):
        """Gibt eine Zeile im Boot-Sequenz-Stil aus"""
        status = "  [ ✅ ]  " if success else "  [ ❌ ]  "
        # Padding für die Nachricht, damit die Status-Symbole untereinander stehen
        print(f"{status} {message}")

    def run_pre_checks(self):
        """Prüft die Infrastruktur und Pfade"""
        print(f"\n--- Initialisierung Arbeitszeit-Report {self.month:02d}/{self.year} ---")
        
        checks = [
            (f"Root-Verzeichnis ({self.base_path})", os.path.exists(self.base_path)),
            ("Config-Verzeichnis (/config)", os.path.exists(self.config_path)),
            ("Monats-Basisordner (/months)", os.path.exists(os.path.join(self.base_path, "months"))),
            (f"Daten für Monat {self.month:02d}", os.path.exists(self.months_path))
        ]
        
        for msg, result in checks:
            self.log_step(f"Prüfe {msg}...", result)
            if not result:
                print(f"\nCRITICAL: Abbruch - Struktur unvollständig.")
                sys.exit(1)

    def _validate_numeric_config(self, filename, min_val=0, max_val=None, is_int=False):
        """Validierungshilfe für numerische Dateien"""
        path = os.path.join(self.config_path, filename)
        if not os.path.exists(path):
            self.log_step(f"{filename.ljust(25)} fehlt", False)
            self.errors.append(f"Config: {filename} fehlt")
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read().strip().replace(',', '.')
                if not raw: raise ValueError("Datei leer")
                val = int(raw) if is_int else float(raw)
                
                if val < min_val or (max_val is not None and val > max_val):
                    raise ValueError(f"Wert außerhalb Bereich ({min_val}-{max_val})")
                
                self.log_step(f"{filename.ljust(25)} validiert ({val})")
                return val
        except ValueError:
            self.log_step(f"{filename.ljust(25)} ungültig", False)
            self.errors.append(f"Config: {filename} hat ungültigen Wert")
            return None

    def validate_configs(self):
        """Prüft alle 9 Konfigurationsdateien gemäß Spezifikation"""
        print("\n--- Validierung Konfigurationsdateien ---")
        
        # 1. Numerische Limits und Targets
        self.config['daily_target'] = self._validate_numeric_config(".dailytargethours", min_val=1)
        self.config['daily_limit'] = self._validate_numeric_config(".dailylegallimit", min_val=1, max_val=10)
        self.config['weekly_target'] = self._validate_numeric_config(".weeklytargethours", min_val=1)
        self.config['weekly_limit'] = self._validate_numeric_config(".weeklycompanyhourslimit", min_val=1)
        self.config['vacation'] = self._validate_numeric_config(".vacationdays", min_val=1, is_int=True)
        self.config['special_vacation'] = self._validate_numeric_config(".specialvacationdays", min_val=1, is_int=True)

        # 2. Working Days
        wd_path = os.path.join(self.config_path, ".workingdays")
        if os.path.exists(wd_path):
            with open(wd_path, "r", encoding="utf-8") as f:
                days = [l.strip() for l in f if l.strip()]
                valid_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                if days and all(d in valid_names for d in days) and len(days) == len(set(days)):
                    self.config['working_days'] = days
                    self.log_step(".workingdays               validiert")
                else:
                    self.log_step(".workingdays               ungültig/Duplikate", False)
                    self.errors.append("Config: .workingdays fehlerhaft")
        else:
            self.log_step(".workingdays               fehlt", False)
            self.errors.append("Config: .workingdays fehlt")

        # 3. Holidays
        h_path = os.path.join(self.config_path, ".holidays")
        self.config['holiday_dates'] = []
        if os.path.exists(h_path):
            with open(h_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
                dates = [l.split('|')[0].strip() for l in lines]
                if len(dates) == len(set(dates)):
                    self.config['holiday_dates'] = dates
                    self.log_step(".holidays                  validiert")
                else:
                    self.log_step(".holidays                  Duplikate gefunden", False)
                    self.errors.append("Config: .holidays Dubletten")
        else:
            self.log_step(".holidays                  fehlt (optional)", True)

        # 4. Closing Days
        c_path = os.path.join(self.config_path, ".closingdays")
        self.config['closing_dates'] = []
        if os.path.exists(c_path):
            with open(c_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
                dates = [l.split('|')[0].strip() for l in lines]
                valid_vals = ["0", "1", "0,5", "0.5"]
                vals_ok = all(len(l.split('|')) == 2 and l.split('|')[1].strip() in valid_vals for l in lines)
                
                if len(dates) == len(set(dates)) and vals_ok:
                    self.config['closing_dates'] = dates
                    self.log_step(".closingdays               validiert")
                else:
                    self.log_step(".closingdays               Formatfehler/Dubletten", False)
                    self.errors.append("Config: .closingdays fehlerhaft")
        else:
            self.log_step(".closingdays               fehlt (optional)", True)

        # 5. Cross-Check: Holidays vs Closing Days
        conflict = set(self.config.get('holiday_dates', [])) & set(self.config.get('closing_dates', []))
        if conflict:
            self.log_step(f"KONFLIKT: {conflict}", False)
            self.errors.append(f"Konflikt: Datum in .holidays UND .closingdays")

    def validate_day_files(self):
        """Prüft die inhaltlichen Regeln der Tagesdateien"""
        print(f"\n--- Analyse Tagesdateien ({self.month:02d}/{self.year}) ---")
        
        try:
            files = sorted([f for f in os.listdir(self.months_path) if f.endswith(".txt")], 
                           key=lambda x: int(x.split('.')[0]))
        except ValueError:
            self.log_step("Dateinamen-Format ungültig", False)
            self.errors.append("Dateinamen müssen Zahlen sein (1.txt, 2.txt...)")
            return

        if not files:
            self.log_step("Keine Daten vorhanden", False)
            return

        for filename in files:
            file_path = os.path.join(self.months_path, filename)
            day_num = filename.replace(".txt", "")
            
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
            
            # Analyse Inhalt
            markers = ["Krank", "Urlaub", "Sonderurlaub", "GLZ"]
            found_markers = [l for l in lines if l in markers]
            work_blocks = [l for l in lines if l.startswith("-") and "Pause" not in l]
            pause_blocks = [l for l in lines if l.startswith("-") and "Pause" in l]

            # Regel-Prüfung
            file_errors = []
            if len(found_markers) > 1: file_errors.append("Mehrere Marker")
            if found_markers and (work_blocks or pause_blocks): file_errors.append("Mix Marker/Blöcke")
            if pause_blocks and not work_blocks: file_errors.append("Nur Pausen")
            
            # Zeit-Dubletten-Check (Einfach)
            times = [l.split('|')[0].strip() for l in (work_blocks + pause_blocks)]
            if len(times) != len(set(times)): file_errors.append("Doppelte Zeitblöcke")

            if not file_errors:
                self.log_step(f"Tag {day_num.ljust(2)} ({filename.ljust(6)}) : OK")
            else:
                err_str = ", ".join(file_errors)
                self.log_step(f"Tag {day_num.ljust(2)} ({filename.ljust(6)}) : FEHLER ({err_str})", False)
                self.errors.append(f"Datei {filename}: {err_str}")

    def print_summary(self):
        print("\n" + "="*50)
        if not self.errors:
            print("  ZUSAMMENFASSUNG: SYSTEM BEREIT FÜR BERECHNUNG")
            print("  Alle Validierungen erfolgreich abgeschlossen. ✅")
        else:
            print(f"  ZUSAMMENFASSUNG: {len(self.errors)} FEHLER GEFUNDEN ❌")
            print("-"*50)
            for err in self.errors:
                print(f"  -> {err}")
        print("="*50 + "\n")

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
    tracker.print_summary()

if __name__ == "__main__":
    main()