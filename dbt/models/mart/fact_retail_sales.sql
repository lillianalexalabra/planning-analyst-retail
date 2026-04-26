-- dbt/models/mart/fact_retail_sales.sql
{{
    config(materialized='table')
}}

WITH stg AS (
    SELECT * FROM {{ ref('stg_census_retail') }}
),

with_lags AS (
    SELECT
        period,
        category_code,
        data_type_code,
        seasonally_adj,
        sales_millions,
        LAG(sales_millions)     OVER (
            PARTITION BY category_code, data_type_code
            ORDER BY period
        ) AS prev_month_sales,
        LAG(sales_millions, 12) OVER (
            PARTITION BY category_code, data_type_code
            ORDER BY period
        ) AS prev_year_sales
    FROM stg
)

SELECT
    period,
    category_code,
    data_type_code,
    seasonally_adj,
    'US'                                                               AS region_code,
    sales_millions,
    CASE
        WHEN prev_month_sales > 0
        THEN (sales_millions - prev_month_sales) / prev_month_sales
        ELSE NULL
    END                                                                AS month_over_month_pct,
    CASE
        WHEN prev_year_sales > 0
        THEN (sales_millions - prev_year_sales) / prev_year_sales
        ELSE NULL
    END                                                                AS year_over_year_pct
FROM with_lags
