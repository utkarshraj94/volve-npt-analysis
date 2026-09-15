import os
import re
import pandas as pd

WELLBORE_RE = re.compile(r"^15/9-(?:(?P<num>F-\d+)|(?P<explore>19))(?: (?P<suffix>.+))?$")

REPORTS_PATH = os.path.join("data", "interim", "drilling_reports.parquet")
PRODUCTION_PATH = os.path.join("data", "interim", "production_clean.parquet")
OUT_PATH = os.path.join("data", "reference", "wellbore_map.csv")


def parse_wellbore(well_name_raw):
    m = WELLBORE_RE.match(well_name_raw)
    if not m:
        raise ValueError(f"Unexpected wellbore name format: {well_name_raw}")
    base = m.group("num") or m.group("explore")
    suffix = m.group("suffix")
    wellbore_key = base if suffix is None else f"{base}-{suffix}"
    return wellbore_key, base, suffix or ""


if __name__ == "__main__":
    reports = pd.read_parquet(REPORTS_PATH)
    pairs = reports[["well_name_file", "well_name_raw"]].drop_duplicates()

    production = pd.read_parquet(PRODUCTION_PATH)
    production_wellbores = set(production["NPD_WELL_BORE_NAME"].unique())

    rows = []
    for _, row in pairs.iterrows():
        wellbore_key, parent_well, sidetrack = parse_wellbore(row["well_name_raw"])
        rows.append({
            "well_name_raw": row["well_name_raw"],
            "well_name_file": row["well_name_file"],
            "wellbore_key": wellbore_key,
            "parent_well": parent_well,
            "sidetrack": sidetrack,
            "has_production_data": row["well_name_raw"] in production_wellbores,
        })

    wellbore_map = pd.DataFrame(rows).sort_values(["parent_well", "sidetrack"])

    os.makedirs("data/reference", exist_ok=True)
    wellbore_map.to_csv(OUT_PATH, index=False)

    print(wellbore_map.to_string(index=False))
    print(f"\nWrote {len(wellbore_map)} rows to {OUT_PATH}")
    print(f"Wellbores with production data: {wellbore_map['has_production_data'].sum()} of {len(wellbore_map)}")