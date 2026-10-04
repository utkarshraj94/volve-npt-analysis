import json
import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD'))}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

RATE = 12500  # assumed $ per rig-hour (same as sql/03_transforms.sql)
OUT = Path("docs/dashboard/data.json")


def rows(conn, sql):
    return [dict(r._mapping) for r in conn.execute(text(sql))]


with engine.connect() as conn:
    k = rows(conn, """
        SELECT SUM(a.hours)                                         AS total_hours,
               SUM(a.hours) FILTER (WHERE a.is_npt_final)           AS npt_hours,
               SUM(a.hours) FILTER (WHERE c.is_rig_move)            AS rig_move_hours
        FROM fact_drilling_activity a
        JOIN dim_npt_category c ON a.npt_cat_id = c.npt_cat_id
    """)[0]
    k = {key: float(v) for key, v in k.items()}
    k["productive_hours"] = k["total_hours"] - k["npt_hours"] - k["rig_move_hours"]
    k["npt_pct"] = 100 * k["npt_hours"] / k["total_hours"]
    k["npt_cost_usd"] = k["npt_hours"] * RATE

    pareto = rows(conn, """
        SELECT level1, level2, npt_hours, pct_of_total_npt, cumulative_pct
        FROM v_npt_pareto
    """)

    wellbores = rows(conn, """
        SELECT wellbore_key, parent_well, is_exploration, total_hours, npt_hours,
               ROUND(100 * npt_hours / NULLIF(total_hours, 0), 2) AS npt_pct
        FROM v_npt_by_wellbore
        ORDER BY npt_pct DESC
    """)

    by_year = rows(conn, """
        SELECT d.year,
               SUM(a.hours) FILTER (WHERE a.is_npt_final) AS npt_hours,
               SUM(a.hours)                               AS total_hours,
               ROUND(100 * SUM(a.hours) FILTER (WHERE a.is_npt_final) / SUM(a.hours), 2) AS npt_pct
        FROM fact_drilling_activity a
        JOIN dim_date d ON a.report_date = d.date_key
        GROUP BY d.year
        ORDER BY d.year
    """)

    producers = rows(conn, """
        SELECT n.wellbore_key,
               ROUND(100 * n.npt_hours / n.total_hours, 2) AS npt_pct,
               n.npt_hours,
               p.cum_oil_bbl,
               v.npt_hrs_per_kbbl
        FROM v_npt_by_wellbore n
        JOIN v_wellbore_production p USING (wellbore_key)
        JOIN v_npt_vs_production v   USING (wellbore_key)
        WHERE p.cum_oil_bbl > 0
        ORDER BY p.cum_oil_bbl DESC
    """)

for w in wellbores:
    w["npt_cost_usd"] = float(w["npt_hours"]) * RATE
for p in producers:
    p["npt_cost_usd"] = float(p["npt_hours"]) * RATE

data = {
    "rate_usd_per_hr": RATE,
    "kpis": k,
    "pareto": pareto,
    "wellbores": wellbores,
    "by_year": by_year,
    "producers": producers,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(data, indent=2, default=float), encoding="utf-8")

print(f"wrote {OUT}")
print(f"total hours {k['total_hours']:.1f}, NPT {k['npt_hours']:.1f} ({k['npt_pct']:.2f}%)")
print(f"pareto rows {len(pareto)}, wellbores {len(wellbores)}, years {len(by_year)}, producers {len(producers)}")
