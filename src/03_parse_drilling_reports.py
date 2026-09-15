import os
import re
import glob
import pandas as pd
from bs4 import BeautifulSoup

RAW_DIR = os.path.join("data", "raw", "Well_technical_data", "Daily Drilling Report - HTML Version")
INTERIM_DIR = os.path.join("data", "interim")
DQ_REPORT_PATH = os.path.join("docs", "drilling_reports_data_quality.md")

FILENAME_RE = re.compile(r"^(?P<well>.+)_(?P<year>\d{4})_(?P<month>\d{2})_(?P<day>\d{2})\.html$")
MISSING_SENTINEL = -999.99

def parse_filename(path):
    name = os.path.basename(path)
    m = FILENAME_RE.match(name)
    if not m:
        raise ValueError(f"Unexpected filename format: {name}")
    well_name_file = m.group("well")
    report_date = f"{m.group('year')}-{m.group('month')}-{m.group('day')}"
    return well_name_file, report_date


def clean_numeric(text):
    text = (text or "").strip()
    if text == "":
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return None if value == MISSING_SENTINEL else value

def parse_header(soup):
    well_name_raw = None
    period_text = None
    for b in soup.find_all("b"):
        label = b.get_text(strip=True)
        value = b.parent.get_text(strip=True)[len(label):].strip()
        if label.startswith("Wellbore"):
            well_name_raw = value
        elif label.startswith("Period"):
            period_text = value
    return well_name_raw, period_text


def parse_info_tables(soup):
    info = {}
    for table_id in ["wellboreInfoTable_1", "wellboreInfoTable_2", "wellboreInfoTable_3"]:
        table = soup.find("table", id=table_id)
        if table is None:
            continue
        for tr in table.select("tbody tr"):
            cells = tr.find_all("td")
            if len(cells) < 2:
                continue
            key = cells[0].get_text(strip=True).rstrip(":")
            value = cells[1].get_text(strip=True)
            info[key] = value
    return info

def parse_operations(soup):
    table = soup.find("table", id="operationsInfoTable")
    if table is None:
        return []
    rows = []
    for tr in table.select("tbody tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) != 6:
            continue
        start_time, end_time, end_depth, activity, state, remark = cells
        rows.append({
            "time_from": start_time,
            "time_to": end_time,
            "depth_md_to": clean_numeric(end_depth),
            "activity_raw": activity,
            "state": state,
            "narrative": remark,
        })
    return rows

def compute_hours(time_from, time_to):
    fh, fm = (int(x) for x in time_from.split(":"))
    th, tm = (int(x) for x in time_to.split(":"))
    start_min = fh * 60 + fm
    end_min = th * 60 + tm
    if end_min <= start_min:
        end_min += 24 * 60
    return (end_min - start_min) / 60.0

def build_tables():
    activity_rows = []
    report_rows = []
    skipped_no_ops = []

    for path in sorted(glob.glob(os.path.join(RAW_DIR, "*.html"))):
        well_name_file, report_date = parse_filename(path)
        report_id = f"{well_name_file}_{report_date}"

        with open(path, encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        well_name_raw, period_text = parse_header(soup)
        info = parse_info_tables(soup)

        report_rows.append({
            "report_id": report_id,
            "well_name_file": well_name_file,
            "well_name_raw": well_name_raw,
            "report_date": report_date,
            "period": period_text,
            "report_number": info.get("Report number"),
            "operator": info.get("Operator"),
            "rig_name": info.get("Rig Name"),
            "hole_dia_in": clean_numeric(info.get("Hole Dia (in)")),
            "dist_drilled_m": clean_numeric(info.get("Dist Drilled (m)")),
        })

        ops = parse_operations(soup)
        if not ops:
            skipped_no_ops.append(report_id)
            continue

        prev_depth = None
        for seq, row in enumerate(ops, start=1):
            main_activity, _, sub_activity = row["activity_raw"].partition(" -- ")
            activity_rows.append({
                "report_id": report_id,
                "well_name_file": well_name_file,
                "well_name_raw": well_name_raw,
                "report_date": report_date,
                "seq": seq,
                "time_from": row["time_from"],
                "time_to": row["time_to"],
                "hours": compute_hours(row["time_from"], row["time_to"]),
                "depth_md_from": prev_depth,
                "depth_md_to": row["depth_md_to"],
                "main_activity": main_activity,
                "activity_code": sub_activity or main_activity,
                "state": row["state"],
                "is_npt": row["state"] == "fail",
                "narrative": row["narrative"],
            })
            prev_depth = row["depth_md_to"]

    activity_df = pd.DataFrame(activity_rows)
    reports_df = pd.DataFrame(report_rows)
    return activity_df, reports_df, skipped_no_ops

def add_phase(activity_df, reports_df):
    reports_df = reports_df.copy()
    reports_df["report_date_parsed"] = pd.to_datetime(reports_df["report_date"])
    reports_df = reports_df.sort_values(["well_name_file", "report_date_parsed"])
    reports_df["hole_dia_filled"] = reports_df.groupby("well_name_file")["hole_dia_in"].ffill()

    activity_df = activity_df.copy()
    activity_df["report_date_parsed"] = pd.to_datetime(activity_df["report_date"])

    completion_start = (
        activity_df.loc[activity_df["main_activity"] == "completion"]
        .groupby("well_name_file")["report_date_parsed"]
        .min()
        .rename("completion_start")
    )

    activity_df = activity_df.merge(
        reports_df[["report_id", "hole_dia_filled"]], on="report_id", how="left"
    )
    activity_df = activity_df.merge(completion_start, on="well_name_file", how="left")

    def label(row):
        if row["main_activity"] in ("completion", "plug abandon"):
            return row["main_activity"]
        if pd.notna(row["completion_start"]) and row["report_date_parsed"] >= row["completion_start"]:
            return "post-completion"
        if pd.notna(row["hole_dia_filled"]):
            return f'{row["hole_dia_filled"]:g} in hole'
        return None

    activity_df["phase"] = activity_df.apply(label, axis=1)
    return activity_df.drop(columns=["hole_dia_filled", "completion_start", "report_date_parsed"])

def profile(activity_df, reports_df, skipped_no_ops):
    lines = []
    lines.append(f"Report files found: {len(reports_df)}")
    lines.append(f"Reports with no Operations table: {len(skipped_no_ops)}")
    if skipped_no_ops:
        lines.append("  " + ", ".join(skipped_no_ops))
    lines.append(f"Activity rows parsed: {len(activity_df)}")
    lines.append(f"Distinct wells (filename form): {activity_df['well_name_file'].nunique()}")

    lines.append("\nMain activity value counts:")
    lines.append(activity_df["main_activity"].value_counts().to_string())

    lines.append("\nPhase (hole section) value counts:")
    lines.append(activity_df["phase"].value_counts(dropna=False).to_string())

    lines.append("\nState value counts:")
    lines.append(activity_df["state"].value_counts().to_string())

    npt_hours = activity_df.loc[activity_df["is_npt"], "hours"].sum()
    total_hours = activity_df["hours"].sum()
    lines.append(f"\nNPT (state == fail) hours: {npt_hours:.1f} of {total_hours:.1f} total ({100 * npt_hours / total_hours:.2f}%)")

    hours_per_report = activity_df.groupby("report_id")["hours"].sum()
    off_24 = hours_per_report[(hours_per_report - 24).abs() > 0.01]
    lines.append(f"\nReports where activity hours don't sum to 24h: {len(off_24)} of {len(hours_per_report)}")

    drilling = activity_df[
        (activity_df["main_activity"] == "drilling") & (activity_df["activity_code"] == "drill")
    ].sort_values(["well_name_file", "report_date", "seq"])
    depth_diff = drilling.groupby("well_name_file")["depth_md_to"].diff()
    non_monotonic = int((depth_diff < -0.01).sum())
    lines.append(f"\nActual-drilling rows where depth decreased vs. the previous drilling row for that well: {non_monotonic} of {len(drilling)}")

    return "\n".join(lines), off_24


if __name__ == "__main__":
    activity_df, reports_df, skipped_no_ops = build_tables()
    activity_df = add_phase(activity_df, reports_df)
    report_text, off_24 = profile(activity_df, reports_df, skipped_no_ops)

    os.makedirs("docs", exist_ok=True)
    with open(DQ_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Drilling Reports Data Quality Report\n\n```\n" + report_text + "\n```\n")
    print(report_text)

    if len(off_24):
        off_24_path = os.path.join("docs", "drilling_hours_not_24.csv")
        off_24.to_csv(off_24_path, header=["total_hours"])
        print(f"\nWrote {len(off_24)} reports with hours != 24 to {off_24_path} — review before finalizing.")

    os.makedirs(INTERIM_DIR, exist_ok=True)
    activity_path = os.path.join(INTERIM_DIR, "drilling_activity.parquet")
    reports_path = os.path.join(INTERIM_DIR, "drilling_reports.parquet")
    activity_df.to_parquet(activity_path, index=False)
    reports_df.to_parquet(reports_path, index=False)
    print(f"\nWrote {len(activity_df)} rows to {activity_path}")
    print(f"Wrote {len(reports_df)} rows to {reports_path}")