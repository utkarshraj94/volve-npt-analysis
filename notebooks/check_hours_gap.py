import pandas as pd

df = pd.read_parquet(r"data\interim\drilling_activity.parquet")

hours_per_report = df.groupby("report_id")["hours"].sum()
off_24 = hours_per_report[(hours_per_report - 24).abs() > 0.01]

print(f"Reports with hours != 24: {len(off_24)} of {len(hours_per_report)}")
print(off_24.describe())

lowest = off_24.sort_values().head(5)
highest = off_24.sort_values().tail(5)

for report_id in list(lowest.index) + list(highest.index):
    sub = df[df["report_id"] == report_id].sort_values("seq")
    print(f"\n{report_id} — total {hours_per_report[report_id]:.2f}h, {len(sub)} row(s)")
    print(sub[["seq", "time_from", "time_to", "hours", "phase", "activity_code", "narrative"]].to_string(index=False))