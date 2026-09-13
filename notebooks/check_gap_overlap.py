import pandas as pd

df = pd.read_parquet(r"data\interim\production_clean.parquet")


def missing_dates(wellbore):
    sub = df[df["NPD_WELL_BORE_NAME"] == wellbore]
    full_range = pd.date_range(sub["DATEPRD"].min(), sub["DATEPRD"].max(), freq="D")
    present = set(sub["DATEPRD"])
    return set(full_range) - present


f12_missing = missing_dates("15/9-F-12")
f14_missing = missing_dates("15/9-F-14")

print("F-12 missing:", len(f12_missing))
print("F-14 missing:", len(f14_missing))
print("Identical missing dates:", f12_missing == f14_missing)