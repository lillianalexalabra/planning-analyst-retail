-- dbt/models/mart/dim_date.sql
{{
    config(materialized='table')
}}

SELECT DISTINCT
    period,
    CAST(LEFT(period, 4) AS INTEGER)                              AS year,
    CAST(RIGHT(period, 2) AS INTEGER)                             AS month,
    CAST(CEIL(CAST(RIGHT(period, 2) AS FLOAT) / 3) AS INTEGER)   AS quarter,
    CASE
        WHEN CAST(RIGHT(period, 2) AS INTEGER) IN (12, 1, 2) THEN 'Winter'
        WHEN CAST(RIGHT(period, 2) AS INTEGER) IN (3, 4, 5)  THEN 'Spring'
        WHEN CAST(RIGHT(period, 2) AS INTEGER) IN (6, 7, 8)  THEN 'Summer'
        ELSE 'Fall'
    END                                                            AS season
FROM {{ ref('stg_census_retail') }}
ORDER BY period
