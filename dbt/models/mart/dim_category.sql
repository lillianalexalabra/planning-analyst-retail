-- dbt/models/mart/dim_category.sql
{{
    config(materialized='table')
}}

SELECT DISTINCT
    category_code,
    CASE category_code
        WHEN '441'   THEN 'Motor Vehicle and Parts Dealers'
        WHEN '442'   THEN 'Furniture and Home Furnishings Stores'
        WHEN '443'   THEN 'Electronics and Appliance Stores'
        WHEN '444'   THEN 'Building Material and Garden Equipment'
        WHEN '445'   THEN 'Food and Beverage Stores'
        WHEN '446'   THEN 'Health and Personal Care Stores'
        WHEN '447'   THEN 'Gasoline Stations'
        WHEN '448'   THEN 'Clothing and Clothing Accessories Stores'
        WHEN '4481'  THEN 'Clothing Stores'
        WHEN '4482'  THEN 'Shoe Stores'
        WHEN '4483'  THEN 'Jewelry, Luggage, and Leather Goods Stores'
        WHEN '451'   THEN 'Sporting Goods, Hobby, Book, and Music Stores'
        WHEN '452'   THEN 'General Merchandise Stores'
        WHEN '4521'  THEN 'Department Stores'
        WHEN '4529'  THEN 'Other General Merchandise Stores'
        WHEN '453'   THEN 'Miscellaneous Store Retailers'
        WHEN '454'   THEN 'Nonstore Retailers'
        WHEN '44X72' THEN 'Retail Trade and Food Services'
        WHEN '44'    THEN 'Retail Trade'
        WHEN '722'   THEN 'Food Services and Drinking Places'
        ELSE category_code
    END AS category_name
FROM {{ ref('stg_census_retail') }}
ORDER BY category_code
