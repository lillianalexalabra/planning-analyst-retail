-- dbt/models/staging/stg_census_retail.sql
{{
    config(materialized='view')
}}

SELECT
    time_slot_id                        AS period,
    category_code,
    data_type_code,
    seasonally_adj,
    error_data,
    TRY_CAST(CASE WHEN cell_value = 'Z' THEN '0' ELSE cell_value END AS FLOAT) AS sales_millions,
    _loaded_at
FROM {{ source('raw', 'census_retail_sales') }}
WHERE cell_value IS NOT NULL
  AND cell_value NOT IN ('(NA)', '(S)', '(D)', '(X)')
  AND time_slot_id IS NOT NULL
  AND time_slot_id != '0'
