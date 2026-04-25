---
title: Milestone 1 — Extract & Load Design
date: 2026-04-25
topic: milestone1-extract-load
---

# Milestone 1 — Extract & Load Design

## Scope

Load both data sources into Snowflake `RAW` schema. No transformation, no orchestration, no dashboard.

**Deliverables:**
- `extract/load_census.py` — Census MRTS API → `RAW.CENSUS_RETAIL_SALES`
- `extract/load_firecrawl.py` — Firecrawl scrape → `RAW.FIRECRAWL_PAGES` + `knowledge/raw/`
- `extract/.env.example` — env var template (committed)
- `extract/requirements.txt` — Python dependencies

In this session, `load_firecrawl.py` will also be executed so data lands in Snowflake today.

## Architecture

Two standalone scripts in `extract/`. Each manages its own Snowflake connection, reads from env vars, and is independently runnable.

```
extract/
├── load_census.py
├── load_firecrawl.py
├── .env.example
└── requirements.txt
```

No shared modules — Approach A (two standalone scripts). Small amount of repeated connection boilerplate is acceptable at this scope.

## Source 1 — US Census Bureau Monthly Retail Trade API

**Endpoint:** `https://api.census.gov/data/timeseries/eits/marts`  
**Auth:** None required  
**Categories:** Clothing & accessories (NAICS 448), General merchandise (NAICS 452)  
**Date range:** 2019–present  

**Script logic (`load_census.py`):**
1. Read Snowflake env vars → open connection
2. Call Census MRTS API for target NAICS categories, 2019–present
3. Parse JSON array response into list of row dicts
4. `CREATE TABLE IF NOT EXISTS RAW.CENSUS_RETAIL_SALES`
5. `TRUNCATE` then bulk insert (idempotent — same data for a given date range)
6. Print row count and exit

**Load strategy:** Truncate + reload on every run.

## Source 2 — Firecrawl Web Scrape

**Tool:** Firecrawl Python client (`firecrawl-py`) + Firecrawl MCP server in this session  
**Targets (~5–8 URLs for milestone):**
- SKIMS brand/product pages (skims.com)
- Business of Fashion market coverage (businessoffashion.com)
- Vogue Business industry articles (voguebusiness.com)
- NRF retail industry reports (nrf.com)

**Script logic (`load_firecrawl.py`):**
1. Read env vars (Snowflake + `FIRECRAWL_API_KEY`) → open connection
2. Iterate hardcoded list of target URLs
3. Per URL: call Firecrawl API → get markdown content
4. Write markdown to `knowledge/raw/<slug>.md`
5. `CREATE TABLE IF NOT EXISTS RAW.FIRECRAWL_PAGES`
6. Insert row per page (append strategy — builds scrape history over time)
7. Print summary (URLs scraped, rows loaded)

**Load strategy:** Append each run (preserves scrape history via `scraped_at` timestamp).

## Raw Table Schemas

All columns `VARCHAR` except timestamps — raw layer is a landing zone with no type coercion.

### `RAW.CENSUS_RETAIL_SALES`

| Column | Type | Notes |
|---|---|---|
| `cell_value` | VARCHAR | Sales figure |
| `error_data` | VARCHAR | Margin of error |
| `time_slot_id` | VARCHAR | Period, e.g. "2024-01" |
| `seasonally_adj` | VARCHAR | "yes" or "no" |
| `category_code` | VARCHAR | NAICS-based category |
| `data_type_code` | VARCHAR | "SM" = sales, etc. |
| `geo_level` | VARCHAR | Always "US" for national |
| `_loaded_at` | TIMESTAMP_NTZ | Ingestion timestamp |

### `RAW.FIRECRAWL_PAGES`

| Column | Type | Notes |
|---|---|---|
| `url` | VARCHAR | Source URL |
| `source_name` | VARCHAR | "skims", "businessoffashion", "nrf", etc. |
| `content` | VARCHAR | Full markdown from Firecrawl |
| `scraped_at` | TIMESTAMP_NTZ | When Firecrawl fetched it |
| `_loaded_at` | TIMESTAMP_NTZ | When row was inserted |

## Environment Variables

Stored in `.env` (gitignored). Never committed. Template committed at `extract/.env.example`.

**Status: credentials configured locally as of 2026-04-25.**

```
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_PASSWORD=
SNOWFLAKE_DATABASE=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_ROLE=
FIRECRAWL_API_KEY=
```

## Dependencies (`requirements.txt`)

```
snowflake-connector-python
requests
firecrawl-py
python-dotenv
```

## Constraints

- No credentials committed to git (`.env` is in `.gitignore`)
- Raw layer: no transformations — land data exactly as received
- Scripts must run successfully locally before milestone submission
