-- Volve NPT Analysis — Fact tables
-- Run after 01_ddl_dimensions.sql (dims must exist first).

-- ── fact_drilling_activity ────────────────────────────────────────────
-- Grain: one row per activity line in a daily drilling report (~23 k rows).
CREATE TABLE fact_drilling_activity (
    activity_id           BIGSERIAL    PRIMARY KEY,
    report_id             VARCHAR(40)  NOT NULL,
    wellbore_key          VARCHAR(20)  NOT NULL REFERENCES dim_wellbore(wellbore_key),
    report_date           DATE         NOT NULL REFERENCES dim_date(date_key),
    seq                   SMALLINT     NOT NULL,
    time_from             VARCHAR(5),
    time_to               VARCHAR(5),
    hours                 NUMERIC(6,2) NOT NULL,
    depth_md_from         NUMERIC(8,1),
    depth_md_to           NUMERIC(8,1),
    phase_key             VARCHAR(40)  REFERENCES dim_hole_phase(phase_key),
    npt_cat_id            INTEGER      NOT NULL REFERENCES dim_npt_category(npt_cat_id),
    main_activity         VARCHAR(60),
    activity_code         VARCHAR(60),
    state                 VARCHAR(20),
    confidence            VARCHAR(10),
    classification_source VARCHAR(10),
    is_npt_final          BOOLEAN      NOT NULL,
    narrative             TEXT
);

CREATE INDEX ix_fda_wellbore ON fact_drilling_activity(wellbore_key);
CREATE INDEX ix_fda_date     ON fact_drilling_activity(report_date);
CREATE INDEX ix_fda_npt_cat  ON fact_drilling_activity(npt_cat_id);

-- ── fact_daily_production ─────────────────────────────────────────────
-- Grain: one row per (calendar day, wellbore) (~15 k rows).
CREATE TABLE fact_daily_production (
    prod_id                  BIGSERIAL    PRIMARY KEY,
    wellbore_key             VARCHAR(20)  REFERENCES dim_wellbore(wellbore_key),
    date_key                 DATE         NOT NULL REFERENCES dim_date(date_key),
    npd_well_bore_code       INTEGER,
    npd_well_bore_name       VARCHAR(30)  NOT NULL,
    on_stream_hrs            NUMERIC(5,2),
    oil_bbl                  NUMERIC(12,3),
    gas_bbl                  NUMERIC(12,3),
    water_bbl                NUMERIC(12,3),
    water_inj_bbl            NUMERIC(12,3),
    water_cut                NUMERIC(7,5),
    flow_kind                VARCHAR(20),
    well_type                VARCHAR(5),
    is_injector              BOOLEAN      NOT NULL DEFAULT FALSE,
    days_since_first_oil     INTEGER,
    avg_downhole_pressure    NUMERIC(10,3),
    avg_downhole_temperature NUMERIC(8,3),
    avg_wht_p                NUMERIC(10,3),
    avg_whp_p                NUMERIC(10,3)
);

CREATE INDEX ix_fdp_wellbore ON fact_daily_production(wellbore_key);
CREATE INDEX ix_fdp_date     ON fact_daily_production(date_key);