import os
import argparse
import shutil
from datetime import datetime, date, timedelta

def parse_args():
    parser = argparse.ArgumentParser(description="Tagesdatei Generator für Arbeitszeit-V1")
    parser.add_argument("--path", required=True, help="Pfad zum Jahresverzeichnis")
    parser.add_argument("--year", type=int, required=True, help="Das Jahr für die Generierung")
    parser.add_argument("--overwrite", action="store_true", help="Benennt existierenden 'months' Ordner um und erstellt neu")
    return parser.parse_args()

def load_config(year_path, filename):
    # Konfigurationen liegen im Unterordner 'config'
    full_path = os.path.join(year_path, "config", filename)
    if not os.path.exists(full_path):
        return []
    with open(full_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def get_days_to_generate(year, working_days_cfg, holidays_cfg, closing_days_cfg):
    target_days = []
    holidays = [h.split('|')[0].strip() for h in holidays_cfg]
    closing_days = [c.split('|')[0].strip() for c in closing_days_cfg]
    
    current_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    while current_date <= end_date:
        day_str = current_date.strftime("%d.%m")
        weekday_name = current_date.strftime("%A")
        
        is_workday = weekday_name in working_days_cfg
        is_holiday = day_str in holidays
        is_closing = day_str in closing_days
        
        if is_workday and not is_holiday and not is_closing:
            target_days.append(current_date)
        current_date += timedelta(days=1)
    return target_days

def main():
    args = parse_args()
    year_path = args.path
    year = args.year
    months_dir = os.path.join(year_path, "months")

    # 1. Prüfung auf existierenden "months" Ordner
    if os.path.exists(months_dir):
        if args.overwrite:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            old_dir_name = os.path.join(year_path, f"months_old_{timestamp}")
            os.rename(months_dir, old_dir_name)
            print(f"Bestehender Ordner wurde umbenannt in: {os.path.basename(old_dir_name)}")
        else:
            print(f"Abbruch: Der Ordner '{months_dir}' existiert bereits.")
            print("Nutze den Parameter --overwrite, um den Ordner automatisch zu sichern und neu zu erstellen.")
            return

    # 2. Konfigurationsdateien aus /config/ laden
    working_days = load_config(year_path, ".workingdays")
    holidays = load_config(year_path, ".holidays")
    closing_days = load_config(year_path, ".closingdays")
    
    if not working_days:
        print(f"Fehler: Keine .workingdays im Pfad {os.path.join(year_path, 'config')} gefunden.")
        return

    # 3. Zielordner anlegen
    os.makedirs(months_dir)
    
    # 4. Generierung
    days_to_create = get_days_to_generate(year, working_days, holidays, closing_days)
    content = "08:30 - 12:00\n12:00 - 13:00 | Pause\n13:00 - 16:30"
    
    count = 0
    for d in days_to_create:
        month_name = d.strftime("%m")
        day_filename = f"{d.day}.txt"
        
        # Pfad: /$year/months/$month/$day.txt
        target_month_path = os.path.join(months_dir, month_name)
        os.makedirs(target_month_path, exist_ok=True)
        
        with open(os.path.join(target_month_path, day_filename), "w", encoding="utf-8") as f:
            f.write(content)
        count += 1
            
    print(f"Erfolg! {count} Tagesdateien wurden in {months_dir} generiert.")

if __name__ == "__main__":
    main()