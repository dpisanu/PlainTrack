import os
import argparse
import shutil
from datetime import datetime, date, timedelta

def parse_args():
    parser = argparse.ArgumentParser(description="Day worksheet generator")
    parser.add_argument("--path", required=True, help="Points to the root folder of the dataset that should be reported. This folder must contain `config/` and `months/`.")
    parser.add_argument("--year", type=int, required=True, help="Defines the calendar year used for internal date calculation.")
    parser.add_argument("--overwrite", action="store_true", help="Rename an existing month folder Benennt existierenden `months`.")
    return parser.parse_args()

def load_config(year_path, filename):
    # Configurations are located in the 'config' subfolder
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

    # 1. Check for the existence of the "months" folder
    if os.path.exists(months_dir):
        if args.overwrite:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            old_dir_name = os.path.join(year_path, f"months_old_{timestamp}")
            os.rename(months_dir, old_dir_name)
            print(f"The existing folder has been renamed to: {os.path.basename(old_dir_name)}")
        else:
            print(f"Abort: The Folder '{months_dir}' exists already.")
            print("Use the --overwrite parameter to automatically back up and recreate the folder.")
            return

    # 2. Load configuration files from /config/
    working_days = load_config(year_path, ".workingdays")
    holidays = load_config(year_path, ".holidays")
    closing_days = load_config(year_path, ".closingdays")
    
    if not working_days:
        print(f"Error: No .workingdays in the path {os.path.join(year_path, 'config')} found.")
        return

    # 3. Create a destination folder
    os.makedirs(months_dir)
    
    # 4. Generating
    days_to_create = get_days_to_generate(year, working_days, holidays, closing_days)
    content = "08:30 - 12:00\n12:00 - 13:00 | break\n13:00 - 16:30"
    
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
            
    print(f"Success! {count} Daily files were saved in {months_dir}.")

if __name__ == "__main__":
    main()