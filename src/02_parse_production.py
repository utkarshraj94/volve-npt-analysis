import os
import pandas as pd

RAW_PATH = os.path.join("data", "raw", "Production_data", "Volve production data.xlsx")
INTERIM_DIR = os.path.join("data", "interim")
DQ_REPORT_PATH = os.path.join("docs", "production_data_quality.md")

SM3_TO_BBL = 6.2898


def load_daily_production():
    return pd.read_excel(RAW_PATH, sheet_name="Daily Production Data")


def profile(df):
    lines = []
    lines.append(f"Row count: {len(df)}")
    lines.append(f"Date range: {df['DATEPRD'].min()} to {df['DATEPRD'].max()}")
    lines.append(f"Distinct wellbores: {df['NPD_WELL_BORE_NAME'].nunique()}")

    null_counts = df.isnull().sum()
    lines.append("\nNulls per column:")
    for col, n in null_counts[null_counts > 0].items():
        lines.append(f"  {col}: {n}")

    dup_count = df.duplicated(subset=["DATEPRD", "NPD_WELL_BORE_CODE"]).sum()
    lines.append(f"\nDuplicate (date, wellbore) rows: {dup_count}")

    mismatch = df[
        ((df["WELL_TYPE"] == "OP") & (df["FLOW_KIND"] != "production")) |
        ((df["WELL_TYPE"] == "WI") & (df["FLOW_KIND"] != "injection"))
    ]
    lines.append(f"\nWELL_TYPE / FLOW_KIND mismatches: {len(mismatch)}")

    for col in ["BORE_OIL_VOL", "BORE_GAS_VOL", "BORE_WAT_VOL"]:
        neg = (df[col] < 0).sum()
        zero = (df[col] == 0).sum()
        lines.append(f"{col}: {neg} negative rows, {zero} zero rows")

    coverage_rows = []
    for wellbore, g in df.groupby("NPD_WELL_BORE_NAME"):
        date_min, date_max = g["DATEPRD"].min(), g["DATEPRD"].max()
        expected_days = (date_max - date_min).days + 1
        coverage_rows.append({
            "wellbore": wellbore,
            "first_date": date_min.date(),
            "last_date": date_max.date(),
            "days_present": g["DATEPRD"].nunique(),
            "expected_days": expected_days,
            "gap_days": expected_days - g["DATEPRD"].nunique(),
        })
    coverage = pd.DataFrame(coverage_rows)
    lines.append("\nDate coverage per wellbore:")
    lines.append(coverage.to_string(index=False))

    return "\n".join(lines), mismatch, coverage


def clean(df):
    df = df.copy()
    df["is_injector"] = df["WELL_TYPE"] == "WI"

    df["oil_bbl"] = df["BORE_OIL_VOL"] * SM3_TO_BBL
    df["gas_bbl"] = df["BORE_GAS_VOL"] * SM3_TO_BBL
    df["water_bbl"] = df["BORE_WAT_VOL"] * SM3_TO_BBL
    df["water_inj_bbl"] = df["BORE_WI_VOL"] * SM3_TO_BBL

    first_oil = (
        df[(~df["is_injector"]) & (df["BORE_OIL_VOL"] > 0)]
        .groupby("NPD_WELL_BORE_CODE")["DATEPRD"]
        .min()
        .rename("first_oil_date")
    )
    df = df.merge(first_oil, on="NPD_WELL_BORE_CODE", how="left")
    df["days_since_first_oil"] = (df["DATEPRD"] - df["first_oil_date"]).dt.days

    denom = df["oil_bbl"].fillna(0) + df["water_bbl"].fillna(0)
    df["water_cut"] = (df["water_bbl"] / denom).where(denom > 0)
    df["water_vol_suspect"] = df["BORE_WAT_VOL"] < 0

    water_bbl_for_cut = df["water_bbl"].clip(lower=0)
    denom = df["oil_bbl"].fillna(0) + water_bbl_for_cut.fillna(0)
    df["water_cut"] = (water_bbl_for_cut / denom).where(denom > 0)

    return df


if __name__ == "__main__":
    df = load_daily_production()
    report_text, mismatch, coverage = profile(df)

    os.makedirs("docs", exist_ok=True)
    with open(DQ_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Production Data Quality Report\n\n```\n" + report_text + "\n```\n")
    print(report_text)

    if len(mismatch):
        mismatch_path = os.path.join("docs", "flow_kind_well_type_mismatch.csv")
        mismatch.to_csv(mismatch_path, index=False)
        print(f"\nWrote {len(mismatch)} mismatch rows to {mismatch_path} — review before finalizing.")

    cleaned = clean(df)
    os.makedirs(INTERIM_DIR, exist_ok=True)
    out_path = os.path.join(INTERIM_DIR, "production_clean.parquet")
    cleaned.to_parquet(out_path, index=False)
    print(f"\nWrote {len(cleaned)} rows to {out_path}")