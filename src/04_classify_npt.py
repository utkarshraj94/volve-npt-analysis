import os
import pandas as pd

ACTIVITY_PATH = os.path.join("data", "interim", "drilling_activity.parquet")
INTERIM_DIR = os.path.join("data", "interim")
DQ_REPORT_PATH = os.path.join("docs", "npt_classification_quality.md")
REVIEW_PATH = os.path.join("docs", "npt_manual_review.csv")

HOLE_INSTABILITY_KEYWORDS = ["pack off", "packed off", "pack-off", "stuck", "loss", "lost"]
SIDETRACK_CORRECTIVE_KEYWORDS = ["stuck", "lost", "junk", "fish", "unable to", "abandon"]
DOWNHOLE_EQUIPMENT_KEYWORDS = ["bha", "mwd", "lwd", "bit", "downhole"]
EXTERNAL_LOGISTICS_KEYWORDS = ["weather", "boat", "helicopter", "logistics", "materials", "parts", "supply"]
LABOR_KEYWORDS = ["strike"]
HSE_PERMIT_KEYWORDS = ["permit", "hse", "safety", "orders", "third party"]
WELLBORE_KEYWORDS = ["stuck", "pack off", "packed off", "loss", "lost", "well control", "kick"]
SURFACE_EQUIPMENT_KEYWORDS = ["repair", "maintenance", "rig equipment", "pump", "generator", "crane", "winch", "failure", "alarm", "fault", "trouble shoot"]

MAIN_ACTIVITY_OVERRIDE = {
    "completion": ("Productive", "Completion", "high"),
    "workover": ("Productive", "Workover", "high"),
}

ACTIVITY_CODE_MAP = {
    "drill": ("Productive", "Drilling", "high"),
    "casing": ("Productive", "Casing/Cementing", "high"),
    "trip": ("Productive", "Tripping", "high"),
    "bop/wellhead equipment": ("Productive", "BOP/Wellhead", "high"),
    "bop activities": ("Productive", "BOP/Wellhead", "high"),
    "survey": ("Productive", "Surveying", "high"),
    "hole open": ("Productive", "Drilling", "high"),
    "pressure detection": ("Productive", "Monitoring", "high"),
    "ream": ("Productive", "Drilling", "medium"),
    "log": ("Productive", "Logging", "high"),
    "drill stem test": ("Productive", "Formation Evaluation", "high"),
    "rft/fit": ("Productive", "Formation Evaluation", "high"),
    "core": ("Productive", "Formation Evaluation", "high"),
    "circulation samples": ("Productive", "Circulating", "high"),
    "waiting on weather": ("NPT - External", "Weather", "high"),
    "fish": ("NPT - Downhole Equipment", "Fishing", "high"),
    "well control": ("NPT - Wellbore", "Well Control", "high"),
    "lost circulation": ("NPT - Wellbore", "Losses", "high"),
    "cement plug": ("Productive", "Plug & Abandon", "high"),
    "cut": ("Productive", "Plug & Abandon", "high"),
    "mill": ("Productive", "Plug & Abandon", "high"),
    "equipment recovery": ("Productive", "Plug & Abandon", "high"),
    "mechanical plug": ("Productive", "Plug & Abandon", "high"),
    "squeeze": ("Productive", "Plug & Abandon", "medium"),
    "perforate": ("Productive", "Perforating", "high"),
    "completion string": ("Productive", "Completion", "high"),
    "test scsssv": ("Productive", "Completion", "high"),
    "sand control": ("Productive", "Completion", "high"),
    "stimulate": ("Productive", "Completion", "high"),
    "wire line": ("Productive", "Wireline", "high"),
    "anchor": ("Rig Move / Mobilization", "Mobilization", "high"),
    "skid": ("Rig Move / Mobilization", "Mobilization", "high"),
    "transit": ("Rig Move / Mobilization", "Mobilization", "high"),
    "position": ("Rig Move / Mobilization", "Mobilization", "high"),
    "rig up/down": ("Rig Move / Mobilization", "Mobilization", "high"),
}


def contains_any(text, keywords):
    return any(kw in text for kw in keywords)


def classify_row(row):
    main_activity = row["main_activity"]
    activity_code = row["activity_code"]
    narrative = (row["narrative"] or "").lower()

    if main_activity in MAIN_ACTIVITY_OVERRIDE:
        level1, level2, confidence = MAIN_ACTIVITY_OVERRIDE[main_activity]
    elif activity_code in ACTIVITY_CODE_MAP:
        level1, level2, confidence = ACTIVITY_CODE_MAP[activity_code]
    elif activity_code == "circulating conditioning":
        if contains_any(narrative, HOLE_INSTABILITY_KEYWORDS):
            level1, level2, confidence = "NPT - Wellbore", "Hole Instability", "medium"
        else:
            level1, level2, confidence = "Productive", "Circulating", "medium"
    elif activity_code == "sidetrack":
        if contains_any(narrative, SIDETRACK_CORRECTIVE_KEYWORDS):
            level1, level2, confidence = "NPT - Wellbore", "Sidetrack (Corrective)", "medium"
        else:
            level1, level2, confidence = "Productive", "Sidetrack (Planned)", "medium"
    elif activity_code in ("repair", "maintain"):
        if contains_any(narrative, DOWNHOLE_EQUIPMENT_KEYWORDS):
            level1, level2, confidence = "NPT - Downhole Equipment", "Failure", "medium"
        else:
            level1, level2, confidence = "NPT - Surface Equipment", "Repair/Maintenance", "medium"
    elif activity_code == "wait":
        if contains_any(narrative, LABOR_KEYWORDS):
            level1, level2, confidence = "NPT - External", "Labor Action", "high"
        elif contains_any(narrative, EXTERNAL_LOGISTICS_KEYWORDS):
            level1, level2, confidence = "NPT - External", "Materials/Logistics", "medium"
        elif contains_any(narrative, HSE_PERMIT_KEYWORDS):
            level1, level2, confidence = "NPT - Other", "HSE/Permits", "medium"
        else:
            level1, level2, confidence = "NPT - Other", "Unspecified Wait", "low"
    elif activity_code == "other":
        if contains_any(narrative, LABOR_KEYWORDS):
            level1, level2, confidence = "NPT - External", "Labor Action", "high"
        elif contains_any(narrative, EXTERNAL_LOGISTICS_KEYWORDS):
            level1, level2, confidence = "NPT - External", "Materials/Logistics", "medium"
        elif contains_any(narrative, WELLBORE_KEYWORDS):
            level1, level2, confidence = "NPT - Wellbore", "Hole Instability", "medium"
        elif contains_any(narrative, SURFACE_EQUIPMENT_KEYWORDS):
            level1, level2, confidence = "NPT - Surface Equipment", "Repair/Maintenance", "medium"
        elif contains_any(narrative, HSE_PERMIT_KEYWORDS):
            level1, level2, confidence = "NPT - Other", "HSE/Permits", "medium"
        elif main_activity == "interruption":
            level1, level2, confidence = "NPT - Other", "Unclassified", "low"
        else:
            level1, level2, confidence = "Productive", f"{main_activity.title()} - Other", "low"
    else:
        level1, level2, confidence = "NPT - Other", "Unclassified", "low"

    if row["is_npt"] and level1 == "Productive":
        level1, level2, confidence = "NPT - Other", f"{level2} (flagged fail)", "high"

    return pd.Series([level1, level2, confidence])

def apply_classification(df):
    result = df.apply(classify_row, axis=1)
    result.columns = ["level1", "level2", "confidence"]
    df = pd.concat([df, result], axis=1)
    df["classification_source"] = "rule"
    return df


def build_review_sample(df, random_state=42, audit_sample_size=150):
    low = df[df["confidence"] == "low"]
    low_npt = low[low["level1"].str.startswith("NPT")]
    low_productive = low[~low["level1"].str.startswith("NPT")]
    low_productive_sample = low_productive.sample(
        n=min(audit_sample_size, len(low_productive)), random_state=random_state
    )

    medium = df[df["confidence"] == "medium"]
    medium_sample = medium.sample(n=min(audit_sample_size, len(medium)), random_state=random_state)

    high = df[df["confidence"] == "high"]
    high_sample = high.sample(n=min(audit_sample_size, len(high)), random_state=random_state)

    review = pd.concat([low_npt, low_productive_sample, medium_sample, high_sample]).sort_values(
        ["well_name_file", "report_date", "seq"]
    )
    return review[[
        "report_id", "well_name_file", "report_date", "seq", "time_from", "time_to",
        "main_activity", "activity_code", "state", "level1", "level2", "confidence", "narrative",
    ]].assign(reviewer_verdict="", reviewer_notes="")


def profile(df, review):
    lines = []
    lines.append(f"Total activity rows classified: {len(df)}")
    lines.append("\nConfidence distribution:")
    lines.append(df["confidence"].value_counts().to_string())

    lines.append("\nLevel 1 distribution (hours):")
    lines.append(df.groupby("level1")["hours"].sum().sort_values(ascending=False).to_string())

    lines.append("\nLevel 1 x Level 2 (hours):")
    lines.append(df.groupby(["level1", "level2"])["hours"].sum().sort_values(ascending=False).to_string())

    npt_hours = df.loc[df["level1"].str.startswith("NPT"), "hours"].sum()
    productive_hours = df.loc[df["level1"] == "Productive", "hours"].sum()
    rigmove_hours = df.loc[df["level1"] == "Rig Move / Mobilization", "hours"].sum()
    total_hours = df["hours"].sum()
    lines.append(f"\nNPT hours: {npt_hours:.1f} ({100 * npt_hours / total_hours:.2f}% of total)")
    lines.append(f"Productive hours: {productive_hours:.1f} ({100 * productive_hours / total_hours:.2f}% of total)")
    lines.append(f"Rig Move / Mobilization hours: {rigmove_hours:.1f} ({100 * rigmove_hours / total_hours:.2f}% of total)")

    low_npt_count = len(df[(df["confidence"] == "low") & (df["level1"].str.startswith("NPT"))])
    low_productive_count = len(df[(df["confidence"] == "low") & (~df["level1"].str.startswith("NPT"))])
    lines.append(f"\nRows flagged for manual review: {len(review)} of {len(df)} total")
    lines.append(f"  Low-confidence, NPT-flavored (100% reviewed): {low_npt_count}")
    lines.append(f"  Low-confidence, Productive-flavored (150-row sample of {low_productive_count}): {min(150, low_productive_count)}")
    lines.append(f"  Medium-confidence (150-row sample of {len(df[df['confidence'] == 'medium'])}): {min(150, len(df[df['confidence'] == 'medium']))}")
    lines.append(f"  High-confidence (150-row sample of {len(df[df['confidence'] == 'high'])}): {min(150, len(df[df['confidence'] == 'high']))}")

    return "\n".join(lines)


if __name__ == "__main__":
    df = pd.read_parquet(ACTIVITY_PATH)
    df = apply_classification(df)

    review = build_review_sample(df)

    report_text = profile(df, review)
    os.makedirs("docs", exist_ok=True)
    with open(DQ_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# NPT Classification Quality Report\n\n```\n" + report_text + "\n```\n")
    print(report_text)

    review.to_csv(REVIEW_PATH, index=False)
    print(f"\nWrote {len(review)} rows to {REVIEW_PATH} for manual review")

    os.makedirs(INTERIM_DIR, exist_ok=True)
    out_path = os.path.join(INTERIM_DIR, "drilling_activity_classified.parquet")
    df.to_parquet(out_path, index=False)
    print(f"\nWrote {len(df)} rows to {out_path}")