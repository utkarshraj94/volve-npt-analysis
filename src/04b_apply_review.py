import os
import pandas as pd

CLASSIFIED_PATH = os.path.join("data", "interim", "drilling_activity_classified.parquet")
REVIEW_PATH = os.path.join("docs", "npt_manual_review.csv")
TAXONOMY_PATH = os.path.join("data", "reference", "npt_taxonomy.csv")
OUT_PATH = os.path.join("data", "interim", "drilling_activity_final.parquet")
DQ_REPORT_PATH = os.path.join("docs", "npt_final_quality.md")

KEEP_RULE_TOKENS = {"", "nan", "agree", "agreed", "ok", "yes", "correct"}


def load_taxonomy():
    tax = pd.read_csv(TAXONOMY_PATH)
    canon = set(zip(tax["level1"], tax["level2"]))
    by_level1 = {}
    for level1, level2 in canon:
        by_level1.setdefault(level1, []).append(level2)
    return canon, by_level1


def canon_key(text):
    return "".join(str(text).lower().split()).replace("-", "").replace("/", "")


def normalize_verdict(raw, by_level1):
    text = " ".join(str(raw).strip().split())
    if text.lower() in KEEP_RULE_TOKENS:
        return None  # keep the rule's original label

    key = canon_key(text)
    level1s = sorted(by_level1, key=len, reverse=True)  # longest first, so "NPT - Other" wins over shorter prefixes

    for level1 in level1s:
        if not key.startswith(canon_key(level1)):
            continue
        rest = key[len(canon_key(level1)):]

        if rest == "":  # only a level1 given
            if len(by_level1[level1]) == 1:
                return (level1, by_level1[level1][0])
            raise ValueError(f"Level-1 '{level1}' given without a level-2, but it has multiple options: {raw!r}")

        for level2 in by_level1[level1]:
            if canon_key(level2) == rest:
                return (level1, level2)

        if rest == "sidetrack":  # bare 'sidetrack' -> the variant valid for this level1
            for level2 in by_level1[level1]:
                if "sidetrack" in level2.lower():
                    return (level1, level2)

        raise ValueError(f"Level-1 '{level1}' matched but level-2 did not: {raw!r}")

    raise ValueError(f"No taxonomy match for verdict: {raw!r}")

def canonicalize_rule_label(level1, level2):
    if level1 == "Productive" and level2.endswith(" - Other"):
        return ("Productive", "Other")
    if level1 == "NPT - Other" and level2.endswith("(flagged fail)"):
        return ("NPT - Other", "Operational Failure")
    return (level1, level2)


def enrich_review(review, by_level1):
    review = review.copy()
    norm = review["reviewer_verdict"].apply(lambda r: normalize_verdict(r, by_level1))
    review["rev_level1"] = [n[0] if n else rule for n, rule in zip(norm, review["level1"])]
    review["rev_level2"] = [n[1] if n else rule for n, rule in zip(norm, review["level2"])]
    review["overridden"] = (review["rev_level1"] != review["level1"]) | (review["rev_level2"] != review["level2"])
    return review


def apply_review(df, review):
    key = ["report_id", "seq"]
    merged = df.merge(review[key + ["rev_level1", "rev_level2"]], on=key, how="left")
    merged["reviewed"] = merged["rev_level1"].notna()
    merged["final_level1"] = merged["rev_level1"].fillna(merged["level1"])
    merged["final_level2"] = merged["rev_level2"].fillna(merged["level2"])

    canon_pairs = merged.apply(lambda r: canonicalize_rule_label(r["final_level1"], r["final_level2"]), axis=1)
    merged["final_level1"] = [p[0] for p in canon_pairs]
    merged["final_level2"] = [p[1] for p in canon_pairs]

    merged["classification_source"] = merged["reviewed"].map({True: "manual", False: "rule"})
    merged["is_npt_final"] = merged["final_level1"].str.startswith("NPT")
    return merged.drop(columns=["rev_level1", "rev_level2"])


def profile(merged, review):
    lines = []
    lines.append(f"Total rows: {len(merged)}")
    lines.append(f"Rows manually reviewed: {int(merged['reviewed'].sum())}")
    lines.append("\nClassification source:")
    lines.append(merged["classification_source"].value_counts().to_string())

    lines.append("\n=== Manual-review error rate by confidence tier ===")
    lines.append("(error rate = % of reviewed rows where the human overrode the rule)")
    for conf in ["high", "medium", "low"]:
        sub = review[review["confidence"] == conf]
        n, o = len(sub), int(sub["overridden"].sum())
        rate = 100 * o / n if n else 0
        lines.append(f"  {conf:6}  reviewed={n:5}  overridden={o:5}  error rate={rate:5.1f}%")

    low = review[review["confidence"] == "low"]
    low_npt = low[low["level1"].str.startswith("NPT")]
    low_prod = low[~low["level1"].str.startswith("NPT")]
    lines.append(f"    low breakdown -- NPT-flavored: reviewed={len(low_npt)} error={100*low_npt['overridden'].mean():.1f}%"
                 f" | Productive-flavored: reviewed={len(low_prod)} error={100*low_prod['overridden'].mean():.1f}%")

    total = merged["hours"].sum()
    rule_npt = merged.loc[merged["level1"].str.startswith("NPT"), "hours"].sum()
    final_npt = merged.loc[merged["is_npt_final"], "hours"].sum()
    lines.append(f"\nNPT hours (rule labels only):  {rule_npt:8.1f} ({100*rule_npt/total:.2f}%)")
    lines.append(f"NPT hours (after review):      {final_npt:8.1f} ({100*final_npt/total:.2f}%)")

    lines.append("\n=== Final Level 1 (hours) ===")
    lines.append(merged.groupby("final_level1")["hours"].sum().sort_values(ascending=False).to_string())
    lines.append("\n=== Final Level 1 x Level 2 (hours) ===")
    lines.append(merged.groupby(["final_level1", "final_level2"])["hours"].sum().sort_values(ascending=False).to_string())

    return "\n".join(lines)


if __name__ == "__main__":
    canon, by_level1 = load_taxonomy()
    df = pd.read_parquet(CLASSIFIED_PATH)
    review = pd.read_csv(REVIEW_PATH, encoding="cp1252")

    review = enrich_review(review, by_level1)
    merged = apply_review(df, review)

    bad = merged[~merged.apply(lambda r: (r["final_level1"], r["final_level2"]) in canon, axis=1)]
    if len(bad):
        raise ValueError(f"{len(bad)} rows have non-canonical final labels: {set(zip(bad['final_level1'], bad['final_level2']))}")

    report_text = profile(merged, review)
    os.makedirs("docs", exist_ok=True)
    with open(DQ_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# NPT Final Classification Report (after manual review)\n\n```\n" + report_text + "\n```\n")
    print(report_text)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    merged.to_parquet(OUT_PATH, index=False)
    print(f"\nWrote {len(merged)} rows to {OUT_PATH}")