# 🛠️ PlainTrack: Generator Guide

The `generator.py` script is a small utility designed to automate the initial setup of your time-tracking structure. Instead of creating hundreds of text files manually, this script does the heavy lifting for you based on your personal configuration.

---

## 🚀 Overview

The generator   
1. scans your configuration to identify valid workdays (.workingdays, .holidays, and .closingdays)
2. and creates a standardized folder (01 to 12)
3. and file structure for the entire year (1.txt to max 31.txt)
4. and populates each work day with a default template (e.g., 08:30 - 16:30 including a break).

### Key Features:
* **Smart Filtering:** Automatically skips weekends, public holidays (from `.holidays`), and company closing days (from `.closingdays`).
* **Safety First:** If a `months/` folder already exists, the script will not overwrite it unless explicitly told to do so.
* **Auto-Backup:** When using the overwrite flag, your existing data is safely renamed with a timestamp backup.
* **Template-Based:** Fills every generated day with a predefined work-block template.

---

## 📋 Usage

Run the script from your terminal within your project root:

### Structure
```bash
python generator.py --path [YOUR_PATH] --year [YYYY] [OPTIONAL_FLAGS]  
```

### Exmpaples
```bash
python generator.py --path ./my-work-logs --year 2026
```

```bash
python generator.py --path ./work-2026 --year 2026 --overwrite
```

### Parameters

| Parameter | Required | Description| 
| --- | --- | --- |
|--path | **Yes** | The absolute or relative path to your year directory (where the config/ folder is located). |
| --year | **Yes** | The four-digit year (e.g., 2026) for which you want to generate logs.  |
| --overwrite | No | Renames the existing months/ folder to months_old_TIMESTAMP and starts fresh.  |

---

## 🛠️ Configuration Dependency
Before running the generator, ensure the following files exist in your config/ directory:

1. .workingdays: To know which days of the week you usually work.
2. .holidays *(Optional)*: To skip public holidays.
3. .closingdays *(Optional)*: To skip company-wide closing days.

---

## 📝 Default Content Template
By default, the script populates every generated .txt file with the following content:
```txt
08:30 - 12:00
12:00 - 13:00 | Pause
13:00 - 16:30
```

*(Note: You can easily change this template by editing the content variable inside the main() function of generator.py.)*