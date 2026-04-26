---
title: dbt Star Schema + GitHub Actions Pipeline Design
date: 2026-04-25
topic: dbt-github-actions
---

# dbt Star Schema + GitHub Actions Pipeline Design

## Scope

Build the dbt transformation layer (staging + mart star schema) and automate the full pipeline via GitHub Actions. Together these complete Milestone 01 deliverables 5, 6, and the pipeline diagram requirement.

**Deliverables:**
- `.github/workflows/pipeline.yml` — scheduled full pipeline workflow
- `dbt/dbt_project.yml` — dbt project config
- `dbt/profiles.yml` — Snowflake connection via env vars (committed, no secrets)
- `dbt/models/staging/stg_census_retail.sql` + `schema.yml`
- `dbt/models/mart/dim_date.sql`, `dim_category.sql`, `dim_region.sql`, `fact_retail_sales.sql` + `schema.yml`

## Architecture

Approach A: `profiles.yml` committed to `dbt/` using `{{ env_var() }}` for all credentials. Identical local/CI invocation: `dbt run --profiles-dir . --project-dir dbt`. Secrets come from `.env` locally and GitHub Secrets in CI.

GitHub Actions runs the full pipeline in sequence: extract → load → dbt run → dbt test.

## GitHub Actions Workflow

**File:** `.github/workflows/pipeline.yml`

**Triggers:**
- `schedule`: cron `0 6 5 * *` — 6 AM UTC on the 5th of every month
- `workflow_dispatch`: manual trigger from GitHub UI

**Job steps:**
1. `actions/checkout@v4`
2. `actions/setup-python@v5` (Python 3.11)
3. `pip install -r extract/requirements.txt`
4. `python extract/load_census.py`
5. `pip install dbt-snowflake`
6. `dbt run --profiles-dir . --project-dir dbt`
7. `dbt test --profiles-dir . --project-dir dbt`

**Secrets (GitHub repo Settings → Secrets and variables → Actions):**
All 6 passed as environment variables to the job:
`SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_ROLE`

## dbt Project Structure

```
dbt/
├── dbt_project.yml
├── profiles.yml
└── models/
    ├── staging/
    │   ├── schema.yml
    │   └── stg_census_retail.sql
    └── mart/
        ├── schema.yml
        ├── dim_date.sql
        ├── dim_category.sql
        ├── dim_region.sql
        └── fact_retail_sales.sql
```

## Model Specifications

### `stg_census_retail` (view)

Source: `RAW.CENSUS_RETAIL_SALES`

Transformations:
- Rename `time_slot_id` → `period` (YYYY-MM string)
- Cast `cell_value` to FLOAT as `sales_millions`
- Pass through `category_code`, `data_type_code`, `seasonally_adj`, `error_data`, `_loaded_at`
- Filter: `cell_value IS NOT NULL AND cell_value NOT IN ('(NA)', '(S)')` — Census suppression codes
- Filter: `data_type_code = 'SM'` — not seasonally adjusted monthly sales, millions of dollars

### `dim_date` (table)

Source: `{{ ref('stg_census_retail') }}`

Columns:
- `period` (PK) — YYYY-MM string, e.g. `2024-01`
- `year` — INTEGER
- `month` — INTEGER (1–12)
- `quarter` — INTEGER (1–4), derived as `CEIL(month / 3.0)`
- `season` — VARCHAR: Winter (Dec–Feb), Spring (Mar–May), Summer (Jun–Aug), Fall (Sep–Nov)

### `dim_category` (table)

Source: `{{ ref('stg_census_retail') }}`

Columns:
- `category_code` (PK) — VARCHAR, e.g. `448`
- `category_name` — VARCHAR, human-readable NAICS label (CASE mapping)

Key mappings:
- `448` → Clothing and Clothing Accessories Stores
- `452` → General Merchandise Stores
- `441` → Motor Vehicle and Parts Dealers
- `442` → Furniture and Home Furnishings Stores
- `443` → Electronics and Appliance Stores
- `444` → Building Material and Garden Equipment
- `445` → Food and Beverage Stores
- `446` → Health and Personal Care Stores
- `447` → Gasoline Stations
- `451` → Sporting Goods, Hobby, Book, and Music
- `453` → Miscellaneous Store Retailers
- `454` → Nonstore Retailers
- `722` → Food Services and Drinking Places
- All others → `category_code` as-is (fallback)

### `dim_region` (table)

Static single row:
- `region_code` (PK) — `'US'`
- `region_name` — `'United States'`
- `region_type` — `'National'`

### `fact_retail_sales` (table)

Source: `{{ ref('stg_census_retail') }}`

Columns:
- `period` (FK → dim_date)
- `category_code` (FK → dim_category)
- `region_code` (FK → dim_region) — hardcoded `'US'`
- `sales_millions` — FLOAT
- `month_over_month_pct` — FLOAT, window function: `(sales - LAG(sales,1)) / LAG(sales,1)` partitioned by `category_code`, ordered by `period`
- `year_over_year_pct` — FLOAT, window function: `(sales - LAG(sales,12)) / LAG(sales,12)` partitioned by `category_code`, ordered by `period`

## Tests

### `models/staging/schema.yml`

Source definition for `RAW.CENSUS_RETAIL_SALES` + tests on `stg_census_retail`:
- `period`: `not_null`
- `category_code`: `not_null`
- `sales_millions`: `not_null`

### `models/mart/schema.yml`

- `dim_date.period`: `not_null`, `unique`
- `dim_category.category_code`: `not_null`, `unique`
- `dim_region.region_code`: `not_null`, `unique`
- `fact_retail_sales`: `not_null` on `period`, `category_code`, `sales_millions`

## dbt Profiles

```yaml
# dbt/profiles.yml
planning_analyst_retail:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      database: "{{ env_var('SNOWFLAKE_DATABASE') }}"
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      role: "{{ env_var('SNOWFLAKE_ROLE') }}"
      schema: MARTS
      threads: 4
```

All dbt models (staging views and mart tables) materialize to the `MARTS` schema in Snowflake. No custom schema overrides — keeps setup simple and avoids dbt schema-naming complexity.

## Local Run Commands

```bash
# from project root
source .venv/bin/activate
pip install dbt-snowflake   # one-time, add to requirements.txt

cd dbt
dbt debug --profiles-dir .           # verify connection
dbt run --profiles-dir .             # run all models
dbt test --profiles-dir .            # run all tests
```

## Constraints

- `profiles.yml` committed to repo — safe because it contains only `env_var()` references, no actual credentials
- `dbt-snowflake` added to `extract/requirements.txt` so CI installs it in one step
- GitHub Secrets must be configured before the scheduled workflow can succeed
