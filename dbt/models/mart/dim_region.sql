-- dbt/models/mart/dim_region.sql
{{
    config(materialized='table')
}}

SELECT
    'US'            AS region_code,
    'United States' AS region_name,
    'National'      AS region_type
