CREATE OR REPLACE VIEW v_npt_by_wellbore AS
SELECT
    w.wellbore_key,
    w.parent_well,
    w.is_sidetrack,
    w.has_prod_data,
    w.is_exploration,
    SUM(a.hours)                                                              AS total_hours,
    SUM(a.hours) FILTER (WHERE a.is_npt_final)                               AS npt_hours,
    SUM(a.hours) FILTER (WHERE c.is_rig_move)                                AS rig_move_hours,
    SUM(a.hours) FILTER (WHERE NOT a.is_npt_final AND NOT c.is_rig_move)     AS productive_hours,
    ROUND(
        100.0 * SUM(a.hours) FILTER (WHERE a.is_npt_final)
        / NULLIF(SUM(a.hours) FILTER (WHERE NOT c.is_rig_move), 0),
    2) AS npt_pct
FROM fact_drilling_activity a
JOIN dim_wellbore     w ON a.wellbore_key = w.wellbore_key
JOIN dim_npt_category c ON a.npt_cat_id   = c.npt_cat_id
GROUP BY w.wellbore_key, w.parent_well, w.is_sidetrack, w.has_prod_data, w.is_exploration;

CREATE OR REPLACE VIEW v_npt_pareto AS
SELECT
    c.level1,
    c.level2,
    SUM(a.hours)                                                          AS npt_hours,
    ROUND(100.0 * SUM(a.hours) / SUM(SUM(a.hours)) OVER (), 2)           AS pct_of_total_npt,
    ROUND(
        SUM(SUM(a.hours)) OVER (ORDER BY SUM(a.hours) DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        / SUM(SUM(a.hours)) OVER () * 100
    , 2)                                                                  AS cumulative_pct
FROM fact_drilling_activity a
JOIN dim_npt_category c ON a.npt_cat_id = c.npt_cat_id
WHERE a.is_npt_final
GROUP BY c.level1, c.level2
ORDER BY npt_hours DESC;

CREATE OR REPLACE VIEW v_npt_cost AS
SELECT
    wellbore_key,
    npt_hours,
    ROUND(npt_hours * 12500)            AS npt_cost_usd,
    ROUND(npt_hours * 12500 / 1e6, 2)  AS npt_cost_musd
FROM v_npt_by_wellbore;

CREATE OR REPLACE VIEW v_wellbore_production AS
SELECT
    wellbore_key,
    npd_well_bore_name,
    SUM(oil_bbl)   AS cum_oil_bbl,
    SUM(gas_bbl)   AS cum_gas_bbl,
    SUM(water_bbl) AS cum_water_bbl,
    MIN(date_key)  AS first_prod_date,
    MAX(date_key)  AS last_prod_date,
    COUNT(*)       AS prod_days
FROM fact_daily_production
WHERE NOT is_injector
GROUP BY wellbore_key, npd_well_bore_name;

CREATE OR REPLACE VIEW v_npt_vs_production AS
SELECT
    n.wellbore_key,
    n.npt_pct,
    n.npt_hours,
    n.productive_hours,
    c.npt_cost_usd,
    p.cum_oil_bbl,
    p.prod_days,
    CASE WHEN COALESCE(p.cum_oil_bbl, 0) > 0
         THEN ROUND(n.npt_hours / (p.cum_oil_bbl / 1000.0), 4)
    END AS npt_hrs_per_kbbl
FROM v_npt_by_wellbore   n
JOIN v_npt_cost          c USING (wellbore_key)
LEFT JOIN v_wellbore_production p USING (wellbore_key);