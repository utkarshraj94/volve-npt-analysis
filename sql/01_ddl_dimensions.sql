-- Volve NPT Analysis — Dimension tables
-- Re-running drops and recreates everything (facts first, then dims).

DROP TABLE IF EXISTS fact_daily_production  CASCADE;
DROP TABLE IF EXISTS fact_drilling_activity CASCADE;
DROP TABLE IF EXISTS dim_hole_phase         CASCADE;
DROP TABLE IF EXISTS dim_npt_category       CASCADE;
DROP TABLE IF EXISTS dim_date               CASCADE;
DROP TABLE IF EXISTS dim_wellbore           CASCADE;

-- ── dim_wellbore ─────────────────────────────────────────────────────
CREATE TABLE dim_wellbore (
    wellbore_key   VARCHAR(20) PRIMARY KEY,
    well_name_file VARCHAR(30) NOT NULL,  -- underscore form, e.g. 15_9_F_1_C
    well_name_raw  VARCHAR(30) NOT NULL,  -- slash form,      e.g. 15/9-F-1 C
    parent_well    VARCHAR(20),
    sidetrack      VARCHAR(10),
    is_sidetrack   BOOLEAN NOT NULL DEFAULT FALSE,
    has_prod_data  BOOLEAN NOT NULL DEFAULT FALSE,
    is_exploration BOOLEAN NOT NULL DEFAULT FALSE
);

-- ── dim_npt_category ─────────────────────────────────────────────────
CREATE TABLE dim_npt_category (
    npt_cat_id  SERIAL PRIMARY KEY,
    level1      VARCHAR(50) NOT NULL,
    level2      VARCHAR(50) NOT NULL,
    description TEXT,
    is_npt      BOOLEAN NOT NULL,
    is_rig_move BOOLEAN NOT NULL,
    UNIQUE (level1, level2)
);

-- ── dim_date ──────────────────────────────────────────────────────────
CREATE TABLE dim_date (
    date_key     DATE     PRIMARY KEY,
    year         SMALLINT NOT NULL,
    quarter      SMALLINT NOT NULL,
    month        SMALLINT NOT NULL,
    month_name   VARCHAR(10) NOT NULL,
    week_of_year SMALLINT NOT NULL,
    day_of_week  SMALLINT NOT NULL,  -- ISO: 1=Mon … 7=Sun
    day_name     VARCHAR(10) NOT NULL
);

-- ── dim_hole_phase ────────────────────────────────────────────────────
CREATE TABLE dim_hole_phase (
    phase_key    VARCHAR(40) PRIMARY KEY,
    nominal_diam NUMERIC(5,3),   -- inches; NULL for non-drilling phases
    phase_type   VARCHAR(20) NOT NULL
        CHECK (phase_type IN
               ('drilling','completion','p_and_a','post_completion','unknown'))
);
