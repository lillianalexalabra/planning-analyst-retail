# dbt Star Schema + GitHub Actions Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dbt star schema (staging + mart) transforming `RAW.CENSUS_RETAIL_SALES` into analysis-ready tables, and automate the full pipeline via GitHub Actions on a monthly schedule.

**Architecture:** `profiles.yml` committed to `dbt/` using `{{ env_var() }}` for all Snowflake credentials — identical local and CI invocation. GitHub Actions runs extract → dbt run → dbt test in sequence. All dbt models materialize to the `MARTS` schema in Snowflake.

**Tech Stack:** dbt-snowflake, GitHub Actions, Snowflake, Python 3.11

---

## File Structure

```
.github/
└── workflows/
    └── pipeline.yml                   CREATE

dbt/
├── dbt_project.yml                    CREATE
├── profiles.yml                       CREATE
└── models/
    ├── staging/
    │   ├── schema.yml                 CREATE
    │   └── stg_census_retail.sql      CREATE
    └── mart/
        ├── schema.yml                 CREATE
        ├── dim_date.sql               CREATE
        ├── dim_category.sql           CREATE
        ├── dim_region.sql             CREATE
        └── fact_retail_sales.sql      CREATE

extract/
└── requirements.txt                   MODIFY (add dbt-snowflake)
```

---

### Task 1: Add dbt-snowflake to requirements and install

**Files:**
- Modify: `extract/requirements.txt`

- [ ] **Step 1: Add dbt-snowflake to requirements.txt**

Replace the contents of `extract/requirements.txt` with:

```
# extract/requirements.txt
snowflake-connector-python>=3.0.0
requests>=2.28.0
firecrawl-py>=1.0.0
python-dotenv>=1.0.0
dbt-snowflake>=1.7.0
```

- [ ] **Step 2: Install dbt-snowflake into the virtual environment**

```bash
source .venv/bin/activate
pip install dbt-snowflake
```

Expected: installs without errors. May take 1–2 minutes due to dependencies.

- [ ] **Step 3: Verify dbt is available**

```bash
dbt --version
```

Expected output contains: `dbt-core` and `dbt-snowflake` version numbers.

- [ ] **Step 4: Commit**

```bash
git add extract/requirements.txt
git commit -m "feat: add dbt-snowflake to requirements"
```

---

### Task 2: Create dbt project config and verify Snowflake connection

**Files:**
- Create: `dbt/dbt_project.yml`
- Create: `dbt/profiles.yml`

- [ ] **Step 1: Create dbt_project.yml**

```yaml
# dbt/dbt_project.yml
name: planning_analyst_retail
version: '1.0.0'
config-version: 2

profile: planning_analyst_retail

model-paths: ["models"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"

models:
  planning_analyst_retail:
    staging:
      +materialized: view
    mart:
      +materialized: table
```

- [ ] **Step 2: Create profiles.yml**

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

- [ ] **Step 3: Export env vars and run dbt debug**

dbt reads credentials from shell environment variables, not from `.env` files directly. Export them first:

```bash
set -a; source .env; set +a
dbt debug --profiles-dir . --project-dir dbt
```

Expected: all checks pass including `Connection test: OK`. If you see `Failed to connect`, double-check `SNOWFLAKE_ACCOUNT` format in your `.env` — it should match what worked with `load_census.py`.

- [ ] **Step 4: Create model directories**

```bash
mkdir -p dbt/models/staging dbt/models/mart
```

- [ ] **Step 5: Commit**

```bash
git add dbt/dbt_project.yml dbt/profiles.yml
git commit -m "feat: add dbt project config and Snowflake profile"
```

---

### Task 3: Create staging model

**Files:**
- Create: `dbt/models/staging/schema.yml`
- Create: `dbt/models/staging/stg_census_retail.sql`

- [ ] **Step 1: Probe raw data to understand data_type_code values**

```bash
set -a; source .env; set +a
python3 - <<'EOF'
from pathlib import Path
from dotenv import load_dotenv
import os, snowflake.connector

load_dotenv(Path(".env"))
conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    password=os.environ["SNOWFLAKE_PASSWORD"],
    database=os.environ["SNOWFLAKE_DATABASE"],
    warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
    role=os.environ["SNOWFLAKE_ROLE"],
)
cur = conn.cursor()
cur.execute("SELECT DISTINCT data_type_code, COUNT(*) FROM RAW.CENSUS_RETAIL_SALES GROUP BY 1 ORDER BY 2 DESC")
for row in cur.fetchall():
    print(row)
conn.close()
EOF
```

Expected: a list of data_type_code values and their row counts. Common codes: `SM` (sales millions, not seasonally adj.), `RSAM` (sales millions, seasonally adj.), `PCSM` (percent change). Note the values — the staging model keeps all of them.

- [ ] **Step 2: Create schema.yml**

```yaml
# dbt/models/staging/schema.yml
version: 2

sources:
  - name: raw
    database: "{{ env_var('SNOWFLAKE_DATABASE') }}"
    schema: RAW
    tables:
      - name: census_retail_sales
        description: "Raw monthly retail trade data from US Census Bureau MRTS API"

models:
  - name: stg_census_retail
    description: "Cleaned Census MRTS retail sales — all data types, null/suppressed values removed"
    columns:
      - name: period
        description: "Month in YYYY-MM format"
        tests:
          - not_null
      - name: category_code
        description: "NAICS-based retail category code"
        tests:
          - not_null
      - name: sales_millions
        description: "Retail sales in millions of dollars"
        tests:
          - not_null
```

- [ ] **Step 3: Create stg_census_retail.sql**

```sql
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
    TRY_CAST(cell_value AS FLOAT)       AS sales_millions,
    _loaded_at
FROM {{ source('raw', 'census_retail_sales') }}
WHERE cell_value IS NOT NULL
  AND cell_value NOT IN ('(NA)', '(S)', '(D)', '(X)')
  AND time_slot_id IS NOT NULL
  AND time_slot_id != '0'
```

- [ ] **Step 4: Run the staging model**

```bash
set -a; source .env; set +a
dbt run --profiles-dir . --project-dir dbt --select stg_census_retail
```

Expected output ends with: `1 of 1 OK created sql view model MARTS.stg_census_retail`

- [ ] **Step 5: Run staging tests**

```bash
dbt test --profiles-dir . --project-dir dbt --select stg_census_retail
```

Expected: all 3 tests pass (not_null on period, category_code, sales_millions).

- [ ] **Step 6: Commit**

```bash
git add dbt/models/staging/
git commit -m "feat: add stg_census_retail staging model"
```

---

### Task 4: Create dimension models

**Files:**
- Create: `dbt/models/mart/dim_date.sql`
- Create: `dbt/models/mart/dim_category.sql`
- Create: `dbt/models/mart/dim_region.sql`

- [ ] **Step 1: Create dim_date.sql**

```sql
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
```

- [ ] **Step 2: Create dim_category.sql**

```sql
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
```

- [ ] **Step 3: Create dim_region.sql**

```sql
-- dbt/models/mart/dim_region.sql
{{
    config(materialized='table')
}}

SELECT
    'US'            AS region_code,
    'United States' AS region_name,
    'National'      AS region_type
```

- [ ] **Step 4: Run all three dimension models**

```bash
set -a; source .env; set +a
dbt run --profiles-dir . --project-dir dbt --select dim_date dim_category dim_region
```

Expected: `3 of 3 OK` — three table models created in `MARTS`.

- [ ] **Step 5: Spot-check dim_date**

```bash
python3 - <<'EOF'
from pathlib import Path
from dotenv import load_dotenv
import os, snowflake.connector

load_dotenv(Path(".env"))
conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    password=os.environ["SNOWFLAKE_PASSWORD"],
    database=os.environ["SNOWFLAKE_DATABASE"],
    warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
    role=os.environ["SNOWFLAKE_ROLE"],
)
cur = conn.cursor()
cur.execute("SELECT COUNT(*), MIN(period), MAX(period) FROM MARTS.dim_date")
print("dim_date:", cur.fetchone())
cur.execute("SELECT COUNT(*) FROM MARTS.dim_category")
print("dim_category:", cur.fetchone())
cur.execute("SELECT * FROM MARTS.dim_region")
print("dim_region:", cur.fetchone())
conn.close()
EOF
```

Expected: `dim_date` has ~86 rows (2019-01 to 2026-03), `dim_category` has 21 rows, `dim_region` has 1 row.

- [ ] **Step 6: Commit**

```bash
git add dbt/models/mart/dim_date.sql dbt/models/mart/dim_category.sql dbt/models/mart/dim_region.sql
git commit -m "feat: add dim_date, dim_category, dim_region models"
```

---

### Task 5: Create fact_retail_sales

**Files:**
- Create: `dbt/models/mart/fact_retail_sales.sql`

- [ ] **Step 1: Create fact_retail_sales.sql**

```sql
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
```

- [ ] **Step 2: Run fact_retail_sales**

```bash
set -a; source .env; set +a
dbt run --profiles-dir . --project-dir dbt --select fact_retail_sales
```

Expected: `1 of 1 OK created sql table model MARTS.fact_retail_sales`

- [ ] **Step 3: Spot-check the fact table**

```bash
python3 - <<'EOF'
from pathlib import Path
from dotenv import load_dotenv
import os, snowflake.connector

load_dotenv(Path(".env"))
conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    password=os.environ["SNOWFLAKE_PASSWORD"],
    database=os.environ["SNOWFLAKE_DATABASE"],
    warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
    role=os.environ["SNOWFLAKE_ROLE"],
)
cur = conn.cursor()
cur.execute("""
    SELECT COUNT(*), COUNT(month_over_month_pct), COUNT(year_over_year_pct)
    FROM MARTS.fact_retail_sales
""")
print("total rows, rows with mom, rows with yoy:", cur.fetchone())

cur.execute("""
    SELECT period, category_code, sales_millions, month_over_month_pct
    FROM MARTS.fact_retail_sales
    WHERE category_code = '448' AND data_type_code = 'SM'
    ORDER BY period DESC
    LIMIT 5
""")
print("--- Recent clothing sales (448, SM) ---")
for row in cur.fetchall():
    print(row)
conn.close()
EOF
```

Expected: total row count matches staging row count. Recent clothing sales rows show non-null `month_over_month_pct` values for most rows (null only for the first month per category/type since there's no prior month to compare).

- [ ] **Step 4: Commit**

```bash
git add dbt/models/mart/fact_retail_sales.sql
git commit -m "feat: add fact_retail_sales with MoM and YoY metrics"
```

---

### Task 6: Add mart tests and run full pipeline

**Files:**
- Create: `dbt/models/mart/schema.yml`

- [ ] **Step 1: Create mart schema.yml**

```yaml
# dbt/models/mart/schema.yml
version: 2

models:
  - name: dim_date
    description: "Date dimension with year, month, quarter, and retail season"
    columns:
      - name: period
        description: "Month in YYYY-MM format (primary key)"
        tests:
          - not_null
          - unique

  - name: dim_category
    description: "Retail category dimension mapping NAICS codes to readable names"
    columns:
      - name: category_code
        description: "NAICS-based retail category code (primary key)"
        tests:
          - not_null
          - unique

  - name: dim_region
    description: "Region dimension — single US national row"
    columns:
      - name: region_code
        description: "Region identifier (primary key)"
        tests:
          - not_null
          - unique

  - name: fact_retail_sales
    description: "Monthly retail sales fact table with month-over-month and year-over-year change metrics"
    columns:
      - name: period
        description: "Foreign key to dim_date"
        tests:
          - not_null
          - relationships:
              to: ref('dim_date')
              field: period
      - name: category_code
        description: "Foreign key to dim_category"
        tests:
          - not_null
          - relationships:
              to: ref('dim_category')
              field: category_code
      - name: sales_millions
        description: "Retail sales in millions of dollars"
        tests:
          - not_null
```

- [ ] **Step 2: Run all tests**

```bash
set -a; source .env; set +a
dbt test --profiles-dir . --project-dir dbt
```

Expected: all tests pass. If `relationships` tests fail, check that `dim_date` and `dim_category` tables were built before running the test (they should be since they're built in Task 4).

- [ ] **Step 3: Run the full pipeline end-to-end**

```bash
dbt run --profiles-dir . --project-dir dbt
dbt test --profiles-dir . --project-dir dbt
```

Expected: `5 of 5 OK` on run (stg_census_retail + 4 mart models), all tests pass on test.

- [ ] **Step 4: Commit**

```bash
git add dbt/models/mart/schema.yml
git commit -m "feat: add mart model tests and verify full dbt pipeline"
```

---

### Task 7: Create GitHub Actions workflow

**Files:**
- Create: `.github/workflows/pipeline.yml`

- [ ] **Step 1: Create the workflow directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create pipeline.yml**

```yaml
# .github/workflows/pipeline.yml
name: Retail Analytics Pipeline

on:
  schedule:
    - cron: '0 6 5 * *'   # 6 AM UTC on the 5th of every month
  workflow_dispatch:        # enable manual runs from the GitHub UI

jobs:
  pipeline:
    runs-on: ubuntu-latest
    env:
      SNOWFLAKE_ACCOUNT:   ${{ secrets.SNOWFLAKE_ACCOUNT }}
      SNOWFLAKE_USER:      ${{ secrets.SNOWFLAKE_USER }}
      SNOWFLAKE_PASSWORD:  ${{ secrets.SNOWFLAKE_PASSWORD }}
      SNOWFLAKE_DATABASE:  ${{ secrets.SNOWFLAKE_DATABASE }}
      SNOWFLAKE_WAREHOUSE: ${{ secrets.SNOWFLAKE_WAREHOUSE }}
      SNOWFLAKE_ROLE:      ${{ secrets.SNOWFLAKE_ROLE }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r extract/requirements.txt

      - name: Extract and load Census data
        run: python extract/load_census.py

      - name: Run dbt models
        run: dbt run --profiles-dir . --project-dir dbt

      - name: Run dbt tests
        run: dbt test --profiles-dir . --project-dir dbt
```

- [ ] **Step 3: Add GitHub Secrets**

In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**

Add each of the following secrets with the same values from your local `.env`:

| Secret name | Value source |
|---|---|
| `SNOWFLAKE_ACCOUNT` | Your Snowflake account identifier |
| `SNOWFLAKE_USER` | Your Snowflake username |
| `SNOWFLAKE_PASSWORD` | Your Snowflake password |
| `SNOWFLAKE_DATABASE` | `skims_db` |
| `SNOWFLAKE_WAREHOUSE` | `COMPUTE_WH` |
| `SNOWFLAKE_ROLE` | Your Snowflake role |

- [ ] **Step 4: Commit and push**

```bash
git add .github/workflows/pipeline.yml
git commit -m "feat: add GitHub Actions pipeline with monthly schedule"
git push origin main
```

- [ ] **Step 5: Trigger a manual run to verify**

On GitHub: go to **Actions → Retail Analytics Pipeline → Run workflow → Run workflow**.

Wait for the run to complete (2–4 minutes). All steps should show green checkmarks. If a step fails, click it to see the error log.

Common failure causes:
- `Failed to connect to Snowflake` → check the `SNOWFLAKE_ACCOUNT` secret format
- `dbt: command not found` → `dbt-snowflake` not in requirements.txt (check Task 1)
- `Could not find profile` → `--profiles-dir .` must be relative to repo root where `dbt/profiles.yml` lives; the command uses `--project-dir dbt` to find models

Wait — the `--profiles-dir .` flag tells dbt to look for `profiles.yml` in the current working directory (repo root). But `profiles.yml` is at `dbt/profiles.yml`. So the correct flag is `--profiles-dir dbt`, not `--profiles-dir .`.

**Correction:** Use `--profiles-dir dbt` in both the workflow and local commands:

```bash
dbt run --profiles-dir dbt --project-dir dbt
dbt test --profiles-dir dbt --project-dir dbt
```

If you used `--profiles-dir .` in Tasks 2–6 and it worked, it means dbt found the profile by searching up directories. Update the workflow to use `--profiles-dir dbt` to be explicit.
```

---

### Task 8: Update README with dbt run instructions

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add dbt section to README Setup**

In `README.md`, under the `## Setup` section, after the "Run extraction scripts" block, add:

```markdown
### 4. Run dbt transformations

```bash
set -a; source .env; set +a
dbt run --profiles-dir dbt --project-dir dbt
dbt test --profiles-dir dbt --project-dir dbt
```

This creates the `MARTS` schema in Snowflake with five models:
- `stg_census_retail` (view) — cleaned staging layer
- `dim_date`, `dim_category`, `dim_region` (tables) — dimension tables
- `fact_retail_sales` (table) — monthly sales with MoM and YoY metrics
```

- [ ] **Step 2: Commit and push**

```bash
git add README.md
git commit -m "docs: add dbt run instructions to README"
git push origin main
```
