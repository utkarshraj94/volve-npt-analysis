import os
import pandas as pd
from datetime import date, timedelta
from dotenv import load_dotenv
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text

load_dotenv()

WELLBORE_MAP  = "data/reference/wellbore_map.csv"
TAXONOMY_PATH = "data/reference/npt_taxonomy.csv"
ACTIVITY_PATH = "data/interim/drilling_activity_final.parquet"
PROD_PATH     = "data/interim/production_clean.parquet"

DB_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD'))}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

def load_sql(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def load_dim_wellbore(engine):
    wm = pd.read_csv(WELLBORE_MAP)
    wm["is_sidetrack"]   = wm["sidetrack"].notna() & (wm["sidetrack"].str.strip() != "")
    wm["is_exploration"] = ~wm["well_name_file"].str.startswith("15_9_F")
    rows = wm.rename(columns={"has_production_data": "has_prod_data"})[
        ["wellbore_key","well_name_file","well_name_raw",
         "parent_well","sidetrack","is_sidetrack","has_prod_data","is_exploration"]
    ]
    rows.to_sql("dim_wellbore", engine, if_exists="append", index=False)
    print(f"  dim_wellbore:     {len(rows)} rows")
    return wm[["well_name_file","well_name_raw","wellbore_key"]]


def load_dim_npt_category(engine):
    tax = pd.read_csv(TAXONOMY_PATH)
    tax["is_npt"]      = tax["level1"].str.startswith("NPT")
    tax["is_rig_move"] = tax["level1"] == "Rig Move / Mobilization"
    tax[["level1","level2","description","is_npt","is_rig_move"]].to_sql(
        "dim_npt_category", engine, if_exists="append", index=False
    )
    print(f"  dim_npt_category: {len(tax)} rows")
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT npt_cat_id, level1, level2 FROM dim_npt_category")
        )
        return {(r.level1, r.level2): r.npt_cat_id for r in result}


def load_dim_date(engine):
    start, end = date(1990, 1, 1), date(2017, 1, 1)
    rows, d = [], start
    while d < end:
        rows.append({
            "date_key":     d,
            "year":         d.year,
            "quarter":      (d.month - 1) // 3 + 1,
            "month":        d.month,
            "month_name":   d.strftime("%B"),
            "week_of_year": int(d.strftime("%V")),
            "day_of_week":  d.isoweekday(),
            "day_name":     d.strftime("%A"),
        })
        d += timedelta(days=1)
    pd.DataFrame(rows).to_sql("dim_date", engine, if_exists="append", index=False)
    print(f"  dim_date:         {len(rows)} rows")


def load_dim_hole_phase(engine, activity_df):
    def parse_phase(p):
        if "in hole" in p:
            return (float(p.replace("in hole","").strip()), "drilling")
        return {
            "completion":     (None, "completion"),
            "plug abandon":   (None, "p_and_a"),
            "post-completion":(None, "post_completion"),
        }.get(p, (None, "unknown"))

    phases = sorted(activity_df["phase"].dropna().unique())
    rows = [{"phase_key": p, "nominal_diam": parse_phase(p)[0],
             "phase_type": parse_phase(p)[1]} for p in phases]
    pd.DataFrame(rows).to_sql("dim_hole_phase", engine, if_exists="append", index=False)
    print(f"  dim_hole_phase:   {len(rows)} rows")

def load_fact_drilling(engine, activity_df, wm_df, cat_lookup):
    df = activity_df.merge(wm_df[["well_name_file","wellbore_key"]], on="well_name_file", how="left")
    df["npt_cat_id"]  = [cat_lookup.get((l1, l2))
                         for l1, l2 in zip(df["final_level1"], df["final_level2"])]
    df["report_date"] = pd.to_datetime(df["report_date"]).dt.date
    df["phase_key"]   = df["phase"].where(df["phase"].notna(), None)

    df[[
        "report_id","wellbore_key","report_date","seq",
        "time_from","time_to","hours","depth_md_from","depth_md_to",
        "phase_key","npt_cat_id","main_activity","activity_code","state",
        "confidence","classification_source","is_npt_final","narrative",
    ]].to_sql("fact_drilling_activity", engine, if_exists="append", index=False, chunksize=2000)
    print(f"  fact_drilling_activity:  {len(df)} rows")


def load_fact_production(engine, prod_df, wm_df):
    df = prod_df.merge(
        wm_df[["well_name_raw","wellbore_key"]],
        left_on="NPD_WELL_BORE_NAME", right_on="well_name_raw", how="left"
    )
    df["date_key"] = df["DATEPRD"].dt.date
    df["days_since_first_oil"] = (
    df["days_since_first_oil"]
    .apply(lambda x: None if pd.isna(x) else int(x))
)
    df.rename(columns={
        "NPD_WELL_BORE_CODE":        "npd_well_bore_code",
        "NPD_WELL_BORE_NAME":        "npd_well_bore_name",
        "ON_STREAM_HRS":             "on_stream_hrs",
        "FLOW_KIND":                 "flow_kind",
        "WELL_TYPE":                 "well_type",
        "AVG_DOWNHOLE_PRESSURE":     "avg_downhole_pressure",
        "AVG_DOWNHOLE_TEMPERATURE":  "avg_downhole_temperature",
        "AVG_WHP_P":                 "avg_whp_p",
        "AVG_WHT_P":                 "avg_wht_p",
    }, inplace=True)
    df[[
        "wellbore_key","date_key","npd_well_bore_code","npd_well_bore_name",
        "on_stream_hrs","oil_bbl","gas_bbl","water_bbl","water_inj_bbl","water_cut",
        "flow_kind","well_type","is_injector","days_since_first_oil",
        "avg_downhole_pressure","avg_downhole_temperature","avg_whp_p","avg_wht_p",
    ]].to_sql("fact_daily_production", engine, if_exists="append", index=False, chunksize=2000)
    print(f"  fact_daily_production:   {len(df)} rows")

def main():
    engine = create_engine(DB_URL)

    print("Running DDL...")
    with engine.begin() as conn:
        conn.execute(text(load_sql("sql/01_ddl_dimensions.sql")))
        conn.execute(text(load_sql("sql/02_ddl_facts.sql")))

    print("Loading dimensions...")
    wm_df      = load_dim_wellbore(engine)
    cat_lookup = load_dim_npt_category(engine)
    load_dim_date(engine)
    activity_df = pd.read_parquet(ACTIVITY_PATH)
    load_dim_hole_phase(engine, activity_df)

    print("Loading facts...")
    load_fact_drilling(engine, activity_df, wm_df, cat_lookup)
    prod_df = pd.read_parquet(PROD_PATH)
    load_fact_production(engine, prod_df, wm_df)

    print("Creating views...")
    with engine.begin() as conn:
        conn.execute(text(load_sql("sql/03_transforms.sql")))

    print("\nDone.")

if __name__ == "__main__":
    main()