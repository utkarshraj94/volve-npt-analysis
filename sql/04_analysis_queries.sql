-- Volve NPT Analysis — Named analysis queries
-- Each query is self-contained. Run individually in pgAdmin or via psql.

-- ─────────────────────────────────────────────────────────────────────────────
-- [Q1] NPT Pareto — where did the downtime go?
-- ─────────────────────────────────────────────────────────────────────────────
SELECT level1, level2, npt_hours, pct_of_total_npt, cumulative_pct
FROM v_npt_pareto;


-- ─────────────────────────────────────────────────────────────────────────────
-- [Q2] NPT by wellbore — ranked worst to best
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    wellbore_key,
    parent_well,
    is_exploration,
    has_prod_data,
    ROUND(total_hours,    1) AS total_hrs,
    ROUND(npt_hours,      1) AS npt_hrs,
    ROUND(productive_hours,1) AS productive_hrs,
    npt_pct
FROM v_npt_by_wellbore
ORDER BY npt_pct DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- [Q3] Modelled NPT cost by wellbore ($12,500/hr)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    w.wellbore_key,
    w.npt_pct,
    c.npt_hours,
    c.npt_cost_usd,
    c.npt_cost_musd
FROM v_npt_by_wellbore w
JOIN v_npt_cost c USING (wellbore_key)
ORDER BY npt_cost_usd DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- [Q4] NPT by hole phase — which section was hardest?
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    h.phase_key,
    h.phase_type,
    h.nominal_diam,
    ROUND(SUM(a.hours) FILTER (WHERE a.is_npt_final), 1)     AS npt_hours,
    ROUND(SUM(a.hours) FILTER (WHERE NOT c.is_rig_move), 1)  AS billable_hours,
    ROUND(
        100.0 * SUM(a.hours) FILTER (WHERE a.is_npt_final)
        / NULLIF(SUM(a.hours) FILTER (WHERE NOT c.is_rig_move), 0),
    2) AS npt_pct
FROM fact_drilling_activity a
JOIN dim_npt_category c ON a.npt_cat_id = c.npt_cat_id
JOIN dim_hole_phase   h ON a.phase_key  = h.phase_key
GROUP BY h.phase_key, h.phase_type, h.nominal_diam
ORDER BY npt_hours DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- [Q5] Annual NPT trend — did operations improve over time?
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    d.year,
    ROUND(SUM(a.hours) FILTER (WHERE a.is_npt_final), 1)              AS npt_hours,
    ROUND(SUM(a.hours) FILTER (WHERE NOT c.is_rig_move), 1)           AS billable_hours,
    ROUND(
        100.0 * SUM(a.hours) FILTER (WHERE a.is_npt_final)
        / NULLIF(SUM(a.hours) FILTER (WHERE NOT c.is_rig_move), 0),
    2) AS npt_pct
FROM fact_drilling_activity a
JOIN dim_date         d ON a.report_date = d.date_key
JOIN dim_npt_category c ON a.npt_cat_id  = c.npt_cat_id
GROUP BY d.year
ORDER BY d.year;


-- ─────────────────────────────────────────────────────────────────────────────
-- [Q6] KEY QUESTION: did high-NPT wells deliver more production?
-- npt_hrs_per_kbbl: NPT hours per 1,000 bbl — lower = NPT was more justified
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    wellbore_key,
    ROUND(npt_pct, 2)           AS npt_pct,
    ROUND(npt_hours, 1)         AS npt_hours,
    npt_cost_usd,
    ROUND(cum_oil_bbl / 1e6, 3) AS cum_oil_mbbl,
    npt_hrs_per_kbbl
FROM v_npt_vs_production
WHERE cum_oil_bbl IS NOT NULL
ORDER BY cum_oil_bbl DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- [Q7] NPT concentration — how many wells caused 80% of NPT hours?
-- ─────────────────────────────────────────────────────────────────────────────
WITH ranked AS (
    SELECT
        wellbore_key,
        npt_hours,
        SUM(npt_hours) OVER ()                                     AS total_npt,
        SUM(npt_hours) OVER (ORDER BY npt_hours DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)      AS running_npt
    FROM v_npt_by_wellbore
    WHERE npt_hours > 0
)
SELECT
    wellbore_key,
    ROUND(npt_hours, 1)                           AS npt_hours,
    ROUND(100.0 * npt_hours      / total_npt, 2)  AS pct_of_total,
    ROUND(100.0 * running_npt    / total_npt, 2)  AS cumulative_pct
FROM ranked
ORDER BY npt_hours DESC;