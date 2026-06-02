## ⚙️ Configuration Files

All configuration files are located in the `config/` directory of the respective year folder.

This allows each year to define its own working-time settings, public holidays, company closing days, vacation entitlement, and other rule-relevant values.

```text
workslips/
└── 2025/
    ├── config/
    └── months/
```

Since these are hidden files starting with a dot, ensure your file manager is set to show hidden files.

The report generator validates the required configuration files before processing monthly work logs. Numeric values may use either `.` or `,` as the decimal separator.

### 🕒 Working Hours & Limits

| File                           | Format / Example                                               | Required | Description                                                                                                                                              |
| :----------------------------- | :------------------------------------------------------------- | :------: | :------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`.dailytargethours`**        | `8.0`                                                          |     ✅    | Target working hours per regular working day. Must be greater than or equal to `1`.                                                                      |
| **`.dailylegallimit`**         | `10.0`                                                         |     ✅    | Legal maximum working hours per day. Must be between `1` and `10`.                                                                                       |
| **`.weeklytargethours`**       | `40.0`                                                         |     ✅    | Target working hours per week. Must be greater than or equal to `1`.                                                                                     |
| **`.weeklycompanyhourslimit`** | `50.0`                                                         |     ✅    | Company-defined weekly working time limit. Must be greater than or equal to `1`.                                                                         |
| **`.workingdays`**             | `Monday`<br>`Tuesday`<br>`Wednesday`<br>`Thursday`<br>`Friday` |     ✅    | List of regular working days, one weekday per line. The values must match the weekday names produced by the Python runtime locale, for example `Monday`. |

### 📅 Calendar & Absences

| File                       | Format / Example         | Required | Description                                                                                                                                                                                                      |
| :------------------------- | :----------------------- | :------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`.vacationdays`**        | `30`                     |     ✅    | Regular annual vacation entitlement. Must be an integer greater than or equal to `1`.                                                                                                                            |
| **`.specialvacationdays`** | `0`                      |     ✅    | Annual special leave entitlement. Must be an integer greater than or equal to `0`.                                                                                                                               |
| **`.holidays`**            | `25.12 \| Christmas Day` | Optional | Public holidays, one entry per line. Format: `DD.MM \| Description`. The date is used to remove the day from the monthly target hours; the description can be shown in the report.                               |
| **`.closingdays`**         | `24.12 \| 0.5`           | Optional | Company closing days, one entry per line. Format: `DD.MM \| Vacation deduction`. The date is used to remove the day from the monthly target hours; the value after the pipe can document the vacation deduction. |

### Example

```text
my-work-logs-root/
├── config/
│   ├── .workingdays               # Working weekdays, one per line, e.g. Monday, Tuesday...
│   ├── .dailytargethours          # Daily target working hours, e.g. 8.0
│   ├── .dailylegallimit           # Daily legal working time limit, e.g. 10.0
│   ├── .weeklytargethours         # Weekly target working hours, e.g. 40.0
│   ├── .weeklycompanyhourslimit   # Weekly company-defined working time limit, e.g. 50.0
│   ├── .vacationdays              # Regular vacation days per year, e.g. 30
│   ├── .specialvacationdays       # Special vacation days per year, e.g. 0
│   ├── .holidays                  # Date | Description, e.g. 25.12 | Christmas Day
│   └── .closingdays               # Date | Vacation Deduction, e.g. 24.12 | 0.5
```

*Note* : The date format used by the scripts is DD.MM. Example 25.12 for the 25th of December.
