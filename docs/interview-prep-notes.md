# What I'm prepared to defend in the final interview

- API extraction: `extract/load_census.py` — hits the US Census Bureau MRTS REST API (no auth required), loads monthly clothing sales data into `RAW.CENSUS_RETAIL_SALES` in Snowflake; one row per category per month with sales figure, period, and data type code
- Web scrape extraction: `extract/load_firecrawl.py` — scrapes web sources (SKIMS, Business of Fashion, Vogue Business, NRF, Wikipedia) using Firecrawl, loads content into `RAW.FIRECRAWL_PAGES` and saves markdown files locally to `knowledge/raw/`
- GitHub Actions pipeline: `.github/workflows/pipeline.yml` — runs both extraction scripts and dbt on a monthly schedule via GitHub Actions; Snowflake and Firecrawl credentials stored as GitHub secrets
- dbt staging: `dbt/models/staging/stg_census_retail.sql` — cleans column names, casts types, and filters to only the data needed for the mart layer
- dbt mart — fact table: `dbt/models/mart/fact_retail_sales.sql` — monthly sales fact table with measures: sales in millions, month-over-month percent change, year-over-year percent change
- dbt mart — dimensions: `dbt/models/mart/dim_date.sql`, `dim_category.sql`, `dim_region.sql` — dimension tables for slicing by time, category, and geography; joined to fact table in a star schema
- dbt tests: `dbt/models/mart/schema.yml` — tests run on every model to validate no nulls or duplicates before data reaches the dashboard
- Streamlit dashboard: `dashboard/app.py` — deployed to Streamlit Community Cloud; three tabs: (1) overview showing monthly sales trends by year, (2) seasonal patterns showing average sales by calendar month, (3) inventory implications — color-coded action calendar mapping each month to a planning action: build inventory, peak season, or markdown window
- Knowledge base wiki: `knowledge/wiki/` — three wiki pages (overview, market-landscape, demand-drivers) synthesized by Claude Code from 17 scraped raw sources in `knowledge/raw/`; queryable live in the repo via Claude Code
- Key finding: Q4 runs 24.5% above the annual average; December alone is 60% above a typical month; January demand drops 54% — the steepest single-month cliff in the calendar
- Recommendation: commit purchase orders by October 15 — apparel lead times run 6–8 weeks (production + ocean freight + domestic distribution), so holiday inventory must be locked in before demand is visible; this avoids arriving at peak season understocked with no time to reorder
