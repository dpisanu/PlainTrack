# ⏱️ PlainTrack

-- German --

**PlainTrack** ist ein minimalistischer, lokaler Arbeitszeit-Logger und Report-Generator. Er wandelt einfache Textdateien in hochprofessionelle HTML-Berichte um.

### ✨ Warum PlainTrack?

* **Local First:** Deine Daten gehören dir. Keine Cloud, kein Login, kein Tracking.
* **Plain Text Power:** Erfasse deine Zeiten in simplen `.txt` Dateien. Schnell, einfach, zeitlos.
* **Versionierbar:** Dank des Text-Formats lässt sich dein gesamtes Zeit-Log perfekt mit Git versionieren.
* **Voll anpassbar:** Hinterlege eigene Feiertage, Schließtage und individuelle Arbeitszeitmodelle in einfachen Config-Files.
* **Visuelle Reports:** Generiert detaillierte HTML-Übersichten mit Farbkodierung für Überstunden, Block-Analysen und Pausentracking.

### 🚀 Schnelleinstieg

1. **Struktur anlegen:**
   `months/03/22.txt` (für den 22. März)
2. **Zeit erfassen:**
   Schreibe einfach `08:00 - 12:00` in die Datei.
3. **Report generieren:**
   ```bash
   python plaintrack.py --path ./mydata --year 2026 --month 03
   ```

-- English --

**PlainTrack** is a minimalist, local-first work hours logger and report generator. It transforms simple, versionable text files into professional, high-fidelity HTML reports.

Built for developers and power users who prefer the command line and plain text over bloated web interfaces.

---

## ✨ Core Philosophy

- **Local First:** Your data never leaves your machine. No cloud, no accounts, no tracking.
- **Plain Text Power:** Log your hours in simple `.txt` files. Fast, future-proof, and easy to edit.
- **Git-Ready:** Since every log and config is a flat file, your entire history is perfectly versionable via Git.
- **Regulatory Flexibility:** Fully customizable rules for holidays, closing days, and individual work models.
- **Visual Insights:** Generates clean HTML reports featuring color-coded overtime analysis, work-block statistics, and break tracking.

---

## 🚀 Quick Start

1. **Create the structure:**
   `months/03/22.txt` (for March 22)
2. **Record the time:**
   Simply write `08:00 - 12:00` in the file.
3. **Generate report:**
   ```bash
   python plaintrack.py --path ./mydata --year 2026 --month 03
   ```

---

# Structure your data

```text
my-work-logs-root/
├── config/
│   ├── .workingdays          # e.g., Monday, Tuesday...
│   ├── .dailytargethours     # e.g., 8.0
│   ├── .holidays             # Date | Description
│   └── .closingdays          # Date | Vacation Deduction
└── months/
    └── 03/                   # Month folder
        ├── 01.txt            # Day log: "08:00 - 12:00"
        └── 02.txt            # Day log: "Krank" or "Urlaub"
```

---

# Guides

* [Detailed Configuration Guide here](docs/Configuration.md)
* [Detailed Time Logging Guide here](docs/TimeLogging.md)
* [Detailed Generator Guide here](docs/Generator.md)