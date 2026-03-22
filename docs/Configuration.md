## ⚙️ Configuration Files

All configuration files are located in the `config/` directory. They use a simple, line-based format. Since these are hidden files (starting with a dot), ensure your file manager is set to show hidden files.

### 🕒 Working Hours & Limits

| File | Format / Example | Description |
| :--- | :--- | :--- |
| **`.dailytargethours`** | `8.0` | Your contractual target work hours per day (decimal). Use `.` as a separator. |
| **`.weeklytargethours`** | `40.0` | Your contractual target work hours per week. |
| **`.dailylegallimit`** | `10.0` | The legal maximum of hours you are allowed to work per day. |
| **`.weeklycompanyhourslimit`** | `48.0` | The maximum hours per week allowed by company policy. |
| **`.workingdays`** | `Monday`<br>`Tuesday`... | List of regular work days (one per line, e.g., `Monday`). |

### 📅 Calendar & Absences

| File | Format / Example | Description |
| :--- | :--- | :--- |
| **`.holidays`** | `25.12 | Christmas` | Public holidays. Format: `DD.MM \| Description`. The description is shown in the report. |
| **`.closingdays`** | `31.12 | 0.5` | Company closing days. Format: `DD.MM \| Vacation deduction`. The value after the pipe represents the vacation days to be deducted. |
| **`.vacationdays`** | `30` | Your total annual vacation entitlement. |
| **`.specialvacationdays`** | `2` | Additional special leave days (e.g., for moving or wedding). |
