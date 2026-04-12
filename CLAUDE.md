# CLAUDE.md — Planning Analyst Retail (SKIMS Market)

## Project Overview

This is a portfolio analytics engineering project built for the ISBA 4715 course. It targets the Planning Analyst role at SKIMS and demonstrates end-to-end data engineering and analytics skills: API ingestion, Snowflake data warehousing, dbt transformation, and a Streamlit dashboard.

**Core business question:** How does seasonal demand in the shapewear, loungewear, and intimates category behave — and what does that mean for inventory positioning?

## Tech Stack

| Layer | Tool |
|---|---|
| Data Warehouse | Snowflake |
| Transformation | dbt |
| Orchestration | GitHub Actions |
| Dashboard | Streamlit (deployed to Streamlit Community Cloud) |
| Language | Python, SQL |

## Data Sources

- **Source 1 (API):** US Census Bureau Monthly Retail Trade API — monthly apparel & accessories sales by NAICS category, loaded to Snowflake raw schema
- **Source 2 (Web Scrape):** SKIMS website, Business of Fashion, Vogue Business, NRF reports, comparable brand coverage — feeds the knowledge base

## Star Schema

```
fact_retail_sales
├── date_key        → dim_date     (year, month, quarter, season)
├── category_key    → dim_category (NAICS code, name, subcategory)
├── region_key      → dim_region   (US national + regional)
└── measures: sales_millions, month_over_month_change, year_over_year_change
```

### dbt Layers
- `raw` — raw ingested data, no transformations
- `staging` — `stg_census_retail`: cleaned, renamed, type-cast
- `mart` — `dim_date`, `dim_category`, `dim_region`, `fact_retail_sales`

## Repo Structure

```
planning-analyst-retail/
├── CLAUDE.md
├── .gitignore
├── docs/                  # proposal, job posting, ERD, pipeline diagram
├── extract/               # Python ingestion scripts
├── dbt/                   # dbt project (models, tests, schema.yml)
├── dashboard/             # Streamlit app
└── knowledge/             # knowledge base
    ├── raw/               # scraped source files (15+ from 3+ sites)
    ├── wiki/              # Claude Code-generated synthesis pages
    └── index.md           # index of all wiki pages
```

## Credentials & Secrets

All credentials are stored as environment variables and GitHub Actions secrets. Nothing is committed to the repo.

Required environment variables:
- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_USER`
- `SNOWFLAKE_PASSWORD`
- `SNOWFLAKE_DATABASE`
- `SNOWFLAKE_WAREHOUSE`
- `SNOWFLAKE_ROLE`

## Knowledge Base — Query Conventions

The `knowledge/` folder is the project's knowledge base. When answering questions about SKIMS's market, the fashion planning industry, or domain context:

1. Start with `knowledge/index.md` to find the relevant wiki page(s)
2. Read the relevant wiki pages in `knowledge/wiki/` for synthesized insights
3. Refer to `knowledge/raw/` for primary source material when more detail is needed
4. Cite specific wiki pages or raw sources when answering

**Example queries to try in a demo:**
- "What does my knowledge base say about SKIMS's competitive position?"
- "What are the key demand drivers for shapewear according to my sources?"
- "What inventory challenges does the fashion industry face heading into Q4?"
