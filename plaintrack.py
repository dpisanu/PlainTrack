import os
import argparse
import sys
import calendar

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

    def run_pre_checks(self):
        """Prüft die Infrastruktur und Pfade"""
        print(f"\n--- 1. Initialisierung Arbeitszeit-Report {self.month:02d}/{self.year} ---")
        
        checks = [
            (f"Root-Verzeichnis ({self.base_path})", os.path.exists(self.base_path)),
            ("Config-Verzeichnis (/config)", os.path.exists(self.config_path)),
            ("Monats-Basisordner (/months)", os.path.exists(os.path.join(self.base_path, "months"))),
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
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read().strip().replace(',', '.')
                if not raw: raise ValueError("Datei leer")
                val = int(raw) if is_int else float(raw)
                
                if val < min_val or (max_val is not None and val > max_val):
                    raise ValueError("Bereichsfehler")
                
                self.log_step(f"{filename.ljust(25)} validiert ({val})")
                return val
        except ValueError:
            self.log_step(f"{filename.ljust(25)} ungültig", False)
            self.errors.append(f"Config: {filename} hat ungültigen Wert oder Format")
            return None

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

        # Feiertage & Schließtage
        for cfg_file in [".holidays", ".closingdays"]:
            path = os.path.join(self.config_path, cfg_file)
            key = cfg_file.replace(".", "") + "_dates"
            self.config[key] = []
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f if l.strip()]
                    dates = [l.split('|')[0].strip() for l in lines]
                    if len(dates) == len(set(dates)):
                        self.config[key] = dates
                        self.log_step(f"{cfg_file.ljust(25)} validiert")
                    else:
                        self.log_step(f"{cfg_file.ljust(25)} Duplikate", False)
                        self.errors.append(f"Config: {cfg_file} Dubletten")
            else:
                self.log_step(f"{cfg_file.ljust(25)} fehlt (optional)")

        # Cross-Check Holidays vs Closing Days
        conflict = set(self.config.get('holidays_dates', [])) & set(self.config.get('closingdays_dates', []))
        if conflict:
            self.log_step(f"KONFLIKT: {conflict}", False)
            self.errors.append(f"Konflikt: Datum in .holidays UND .closingdays")

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

        if not raw_files:
            self.log_step("Keine Daten vorhanden", False)
            return

        # Sortierung vorbereiten und auf Bereich prüfen
        sorted_files = []
        for f in raw_files:
            day_part = f.replace(".txt", "")
            try:
                day_val = int(day_part)
                # REGEL: Muss zwischen 1 und Max-Tage des Monats liegen
                if day_val < 1 or day_val > days_in_month:
                    self.log_step(f"Datei {f.ljust(10)} : UNGÜLTIGER TAG (Bereich 1-{days_in_month})", False)
                    self.errors.append(f"Datei {f}: Tag {day_val} existiert nicht im Monat {self.month:02d}.")
                else:
                    sorted_files.append((day_val, f))
            except ValueError:
                self.log_step(f"Datei {f.ljust(10)} : KEINE ZAHL", False)
                self.errors.append(f"Datei {f}: Dateiname muss eine positive Ganzzahl sein.")

        # Inhaltliche Prüfung der validen Dateien
        for day_val, filename in sorted(sorted_files):
            file_path = os.path.join(self.months_path, filename)
            
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
            if pause_blocks and not work_blocks: file_errors.append("Nur Pausen ohne Arbeit")
            
            # Zeit-Dubletten-Check (Einfach)
            times = [l.split('|')[0].strip() for l in (work_blocks + pause_blocks)]
            if len(times) != len(set(times)): file_errors.append("Doppelte Zeitblöcke")

            if not file_errors:
                self.log_step(f"Tag {str(day_val).ljust(2)} ({filename.ljust(6)}) : OK")
            else:
                err_msg = ", ".join(file_errors)
                self.log_step(f"Tag {str(day_val).ljust(2)} ({filename.ljust(6)}) : FEHLER ({err_msg})", False)
                self.errors.append(f"Datei {filename}: {err_msg}")

        # Regel: Mehr Dateien als Kalendertage?
        if len(raw_files) > days_in_month:
            self.errors.append(f"Anzahl Fehler: Ordner enthält {len(raw_files)} Dateien, der Monat hat aber nur {days_in_month} Tage.")

        self.check_and_exit_if_failed("Tagesdateien")

    def print_summary(self):
        print("\n" + "="*60)
        if not self.errors:
            print("  ZUSAMMENFASSUNG: SYSTEM BEREIT FÜR BERECHNUNG")
            print("  Alle Validierungen erfolgreich abgeschlossen. ✅")
        else:
            print(f"  ZUSAMMENFASSUNG: {len(self.errors)} FEHLER GEFUNDEN ❌")
            print("-" * 60)
            for err in self.errors:
                print(f"  -> {err}")
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
    tracker.print_summary()

if __name__ == "__main__":
    main()