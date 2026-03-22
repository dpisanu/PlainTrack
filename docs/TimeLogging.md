# ✍️ Logging Guide for PlainTrack

PlainTrack uses simple `.txt` files to record your work hours. Each day is represented by a single file (e.g., `01.txt`, `22.txt`).

## 📁 File Location
Files must be stored in the following structure:
`months/[MM]/[DD].txt` (Example: `months/03/22.txt` for March 22nd).

---

## 🕒 Recording Work Hours

### Standard Work Blocks
Write your start and end times separated by a dash. You can have multiple blocks per day.
```text
08:00 - 12:30
13:15 - 17:00
```  

### Recording Breaks
To log a break, add the keyword Pause to the line. These hours will be calculated separately and subtracted from your total work time.
```text  
12:30 - 13:00 | Pause
```

### Combining Everything
A typical day file might look like this:
```text  
08:00 - 12:00
12:00 - 12:45 | Pause
12:45 - 17:15
```

---

## 🏖️ Full Day Absences
If you are not working at all, do not leave the file empty. Use one of the following keywords as the only content in the file:

| Keyword | Description |
| --- | --- |
| Krank | Sick leave. Sets Target hours to 0 for that day. |
| Urlaub | Vacation. Sets Target hours to 0 for that day. |
| GLZ | Compensatory time off (Gleitzeitausgleich). Subtracts the target hours from your balance.|  

```text 
Urlaub
```

---
 
## 💡 Pro Tips
* **Version Control:** Since these are plain text files, you can use git commit at the end of every day to keep a permanent, timestamped history of your logs.

* **Notes:** You can add comments after a pipe | in work blocks. Everything after the pipe is ignored unless it contains the keyword "Pause".
Example: 09:00 - 11:00 | Project Deepdive (counts as work).

* **Sonderarbeit:** If you work on a weekend or holiday (days where Target = 0), PlainTrack will automatically flag this as a "Sonderarbeitstag" in the report.