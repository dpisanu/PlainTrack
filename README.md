<p align="center">
  <img src="timetrack_logo.svg" height="250"/>
</p>

# ⏱️ PlainTrack

-- German --

**PlainTrack** ist ein minimalistischer, lokaler Arbeitszeit-Logger und Report-Generator. Er wandelt einfache Textdateien in hochprofessionelle HTML-Berichte um.

### ✨ Warum PlainTrack?

* **Local First:** Deine Daten gehören dir. Keine Cloud, kein Login, kein Tracking.
* **Plain Text Power:** Erfasse deine Zeiten in simplen `.txt` Dateien. Schnell, einfach, zeitlos.
* **Versionierbar:** Dank des Text-Formats lässt sich dein gesamtes Zeit-Log perfekt mit Git versionieren.
* **Datennahe Konfiguration:** Die Konfiguration liegt direkt neben den Arbeitszeitdaten, zu denen sie gehört. So bleiben Regeln, Feiertage, Schließtage, Urlaubsansprüche und Arbeitszeitmodelle nachvollziehbar mit dem jeweiligen Datensatz verbunden.
* **Flexible Auswertungsbereiche:** Durch die Wahl eines anderen Root-Ordners können unterschiedliche Konfigurationsbereiche abgebildet werden. z.B.: pro Jahr, Projekt, Kunde, Arbeitsvertrag, Land oder Organisation.
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

* **Plain Text Power:** Log your hours in simple `.txt` files. Fast, future-proof, and easy to edit.
* **Git-Ready:** Since every log and config is a flat file, your entire history is perfectly versionable via Git.
* **Data-Scoped Configuration:** Configuration lives next to the working-time data it belongs to. This keeps rules, holidays, closing days, vacation entitlements, and work models tied to the exact data set being reported.
* **Flexible Reporting Scopes:** By choosing a different root folder, you can define different configuration scopes. For example per year, project, client, employment contract, country, or organization.
* **Regulatory Flexibility:** Fully customizable rules for holidays, closing days, and individual work models.
* **Visual Insights:** Generates clean HTML reports featuring color-coded overtime analysis, work-block statistics, and break tracking.


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

## 📁 Data Structure

PlainTrack operates with work logs in a file-based yearly structure. Each year has its own `config/` next to its `months/` directory, allowing different working-time rules, vacation entitlements, holidays, company closing days, or contractual settings per year.

```text
my-work-logs-root/
├── config/                        # Configuration folder
└── months/
    └── 03/                        # Month folder
        ├── 01.txt                 # One file per day
```

This means that when generating a report for a specific year, the report generator reads the configuration from that year’s folder:

```bash
python reporter.py --path ./workslips/2025/ --year 2025 --month 03
```

In this example, the configuration is loaded from:

```text
./workslips/2025/config/
```

and the monthly work logs are loaded from:

```text
./workslips/2025/months/03/
```

---

# Guides

* [Detailed Configuration Guide here](docs/Configuration.md)
* [Detailed Time Logging Guide here](docs/TimeLogging.md)
* [Detailed Generator Guide here](docs/Generator.md)