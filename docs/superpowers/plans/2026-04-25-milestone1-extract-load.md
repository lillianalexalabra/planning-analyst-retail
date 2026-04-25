# Milestone 1 — Extract & Load Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Load US Census MRTS data and Firecrawl web scrapes into Snowflake `RAW` schema via two standalone Python scripts.

**Architecture:** Two independent scripts in `extract/` — `load_census.py` fetches the Census Bureau MRTS API and truncate-reloads `RAW.CENSUS_RETAIL_SALES`; `load_firecrawl.py` scrapes target URLs via Firecrawl, appends to `RAW.FIRECRAWL_PAGES`, and writes markdown files to `knowledge/raw/`. No shared modules. Each script reads credentials from a `.env` at the project root.

**Tech Stack:** Python 3, `snowflake-connector-python`, `requests`, `firecrawl-py`, `python-dotenv`

---

## File Structure

```
extract/
├── requirements.txt       CREATE
├── .env.example           EXISTS (already committed)
├── load_census.py         CREATE
└── load_firecrawl.py      CREATE

knowledge/
├── raw/                   CREATE (with .gitkeep)
└── wiki/                  CREATE (with .gitkeep)
```

---

### Task 1: Create requirements.txt and install dependencies

**Files:**
- Create: `extract/requirements.txt`

- [ ] **Step 1: Write requirements.txt**

```
# extract/requirements.txt
snowflake-connector-python>=3.0.0
requests>=2.28.0
firecrawl-py>=1.0.0
python-dotenv>=1.0.0
```

- [ ] **Step 2: Create a virtual environment and install**

Run from the project root:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r extract/requirements.txt
```

Expected: all four packages install without errors. `pip list` should show `snowflake-connector-python`, `firecrawl-py`, `requests`, `python-dotenv`.

- [ ] **Step 3: Add .venv to .gitignore if not already present**

Open `.gitignore` and verify `.venv` is listed. It should already be there under `venv/` — confirm that covers `.venv` as well. If not, add:
```
.venv/
```

- [ ] **Step 4: Commit**

```bash
git add extract/requirements.txt .gitignore
git commit -m "feat: add extract requirements and venv gitignore"
```

---

### Task 2: Verify Snowflake connectivity and create RAW schema

**Files:**
- No new files — run inline Python to verify, then create schema via SQL.

- [ ] **Step 1: Locate your Snowflake account identifier**

Log into Snowflake web UI → bottom-left corner shows your account name. It will look like `xy12345` or `orgname-accountname`. Copy it exactly — this is `SNOWFLAKE_ACCOUNT` in your `.env`.

- [ ] **Step 2: Verify the connection from the command line**

With the virtual environment active, run:
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
cur.execute("SELECT CURRENT_USER(), CURRENT_DATABASE(), CURRENT_WAREHOUSE()")
print(cur.fetchone())
conn.close()
EOF
```

Expected output: a tuple like `('YOURUSER', 'PLANNING_ANALYST_RETAIL', 'COMPUTE_WH')`.

If you get `250001 (08001): Failed to connect` — double-check `SNOWFLAKE_ACCOUNT` format. Try with and without the region suffix (e.g., both `xy12345` and `xy12345.us-east-1`).

- [ ] **Step 3: Create the RAW schema**

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
cur.execute("CREATE SCHEMA IF NOT EXISTS RAW")
print("RAW schema created (or already exists)")
conn.close()
EOF
```

Expected: `RAW schema created (or already exists)`

---

### Task 3: Build load_census.py

**Files:**
- Create: `extract/load_census.py`

- [ ] **Step 1: Probe the Census API to confirm response structure**

Run this one-off check before writing the full script:
```bash
python3 - <<'EOF'
import requests

url = "https://api.census.gov/data/timeseries/eits/marts"
params = {
    "get": "cell_value,error_data,time_slot_id,seasonally_adj,category_code,data_type_code",
    "for": "us:*",
    "time": "2024-01",
}
resp = requests.get(url, params=params, timeout=30)
resp.raise_for_status()
data = resp.json()
print("Headers:", data[0])
print("Sample rows:", data[1:4])
print("Total rows:", len(data) - 1)
EOF
```

Expected: headers row like `['cell_value', 'error_data', 'time_slot_id', 'seasonally_adj', 'category_code', 'data_type_code', 'us']` and several data rows. Note the exact header names — if they differ from this list, update the `CREATE TABLE` columns in Step 2 to match.

- [ ] **Step 2: Write extract/load_census.py**

```python
# extract/load_census.py
from pathlib import Path
from dotenv import load_dotenv
import os
import requests
import snowflake.connector

load_dotenv(Path(__file__).parent.parent / ".env")

CENSUS_URL = "https://api.census.gov/data/timeseries/eits/marts"

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS RAW.CENSUS_RETAIL_SALES (
    cell_value     VARCHAR,
    error_data     VARCHAR,
    time_slot_id   VARCHAR,
    seasonally_adj VARCHAR,
    category_code  VARCHAR,
    data_type_code VARCHAR,
    geo_level      VARCHAR,
    _loaded_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP
)
"""

INSERT_SQL = """
INSERT INTO RAW.CENSUS_RETAIL_SALES
    (cell_value, error_data, time_slot_id, seasonally_adj,
     category_code, data_type_code, geo_level)
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""


def fetch_census():
    params = {
        "get": "cell_value,error_data,time_slot_id,seasonally_adj,category_code,data_type_code",
        "for": "us:*",
        "time": "from 2019-01",
    }
    resp = requests.get(CENSUS_URL, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    headers, *rows = data
    return [dict(zip(headers, row)) for row in rows]


def get_conn():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        role=os.environ["SNOWFLAKE_ROLE"],
    )


def load(rows):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(CREATE_TABLE)
    cur.execute("TRUNCATE TABLE RAW.CENSUS_RETAIL_SALES")
    values = [
        (
            r.get("cell_value"),
            r.get("error_data"),
            r.get("time_slot_id"),
            r.get("seasonally_adj"),
            r.get("category_code"),
            r.get("data_type_code"),
            "US",
        )
        for r in rows
    ]
    cur.executemany(INSERT_SQL, values)
    conn.commit()
    cur.close()
    conn.close()
    return len(values)


if __name__ == "__main__":
    print("Fetching Census MRTS data (2019-present)...")
    rows = fetch_census()
    print(f"Fetched {len(rows)} rows from Census API")
    print("Loading to Snowflake RAW.CENSUS_RETAIL_SALES...")
    count = load(rows)
    print(f"Done — {count} rows loaded")
```

- [ ] **Step 3: Commit**

```bash
git add extract/load_census.py
git commit -m "feat: add Census MRTS extraction script"
```

---

### Task 4: Run load_census.py and verify data in Snowflake

**Files:** No changes — run and verify only.

- [ ] **Step 1: Run the script**

```bash
cd /path/to/planning-analyst-retail
source .venv/bin/activate
python extract/load_census.py
```

Expected output:
```
Fetching Census MRTS data (2019-present)...
Fetched NNNN rows from Census API
Loading to Snowflake RAW.CENSUS_RETAIL_SALES...
Done — NNNN rows loaded
```

`NNNN` will be some number in the hundreds to low thousands. If you get a 404 or empty response from the Census API, the time parameter format may need adjustment — try changing `"from 2019-01"` to `"from+2019-01"` in the params dict.

- [ ] **Step 2: Verify row count in Snowflake**

In Snowflake web UI (or via CLI):
```sql
SELECT COUNT(*), MIN(time_slot_id), MAX(time_slot_id), COUNT(DISTINCT category_code)
FROM RAW.CENSUS_RETAIL_SALES;
```

Expected: row count matches script output, `time_slot_id` spans from ~2019 to recent months, several distinct category codes.

---

### Task 5: Create knowledge/ directory structure

**Files:**
- Create: `knowledge/raw/.gitkeep`
- Create: `knowledge/wiki/.gitkeep`

- [ ] **Step 1: Create directories and .gitkeep files**

```bash
mkdir -p knowledge/raw knowledge/wiki
touch knowledge/raw/.gitkeep knowledge/wiki/.gitkeep
```

- [ ] **Step 2: Commit**

```bash
git add knowledge/raw/.gitkeep knowledge/wiki/.gitkeep
git commit -m "feat: add knowledge/ directory structure"
```

---

### Task 6: Build load_firecrawl.py

**Files:**
- Create: `extract/load_firecrawl.py`

- [ ] **Step 1: Probe Firecrawl on one URL to confirm response structure**

```bash
python3 - <<'EOF'
from pathlib import Path
from dotenv import load_dotenv
import os
from firecrawl import FirecrawlApp

load_dotenv(Path(".env"))
app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])
result = app.scrape_url("https://skims.com/pages/our-story", formats=["markdown"])
print(type(result))
print(dir(result))
# print first 500 chars of content
content = result.markdown if hasattr(result, "markdown") else str(result)
print(content[:500])
EOF
```

Expected: a string of markdown content (brand story text). If `result` doesn't have a `.markdown` attribute, check `result.get("markdown")` or `result["content"]` — adjust `load_firecrawl.py` accordingly in Step 2.

- [ ] **Step 2: Write extract/load_firecrawl.py**

```python
# extract/load_firecrawl.py
from pathlib import Path
from dotenv import load_dotenv
import os
import re
from datetime import datetime, timezone
import snowflake.connector
from firecrawl import FirecrawlApp

load_dotenv(Path(__file__).parent.parent / ".env")

TARGETS = [
    {"url": "https://skims.com/pages/our-story",              "source_name": "skims"},
    {"url": "https://skims.com/collections/shapewear",         "source_name": "skims"},
    {"url": "https://skims.com/collections/bras-and-underwear","source_name": "skims"},
    {"url": "https://www.businessoffashion.com/tags/skims",    "source_name": "businessoffashion"},
    {"url": "https://www.voguebusiness.com/t/skims",           "source_name": "voguebusiness"},
    {"url": "https://nrf.com/research/annual-retail-and-food-services-sales", "source_name": "nrf"},
    {"url": "https://nrf.com/research/monthly-retail-trade",   "source_name": "nrf"},
]

KNOWLEDGE_RAW = Path(__file__).parent.parent / "knowledge" / "raw"

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS RAW.FIRECRAWL_PAGES (
    url         VARCHAR,
    source_name VARCHAR,
    content     VARCHAR,
    scraped_at  TIMESTAMP_NTZ,
    _loaded_at  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP
)
"""

INSERT_SQL = """
INSERT INTO RAW.FIRECRAWL_PAGES (url, source_name, content, scraped_at)
VALUES (%s, %s, %s, %s)
"""


def url_to_slug(url: str) -> str:
    slug = re.sub(r"https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", slug).strip("_")
    return slug[:100]


def scrape(app: FirecrawlApp, url: str) -> str:
    result = app.scrape_url(url, formats=["markdown"])
    if hasattr(result, "markdown") and result.markdown:
        return result.markdown
    if isinstance(result, dict):
        return result.get("markdown") or result.get("content") or ""
    return str(result)


def get_conn():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        role=os.environ["SNOWFLAKE_ROLE"],
    )


if __name__ == "__main__":
    app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(CREATE_TABLE)

    loaded = 0
    for target in TARGETS:
        url, source = target["url"], target["source_name"]
        print(f"Scraping {url} ...")
        try:
            content = scrape(app, url)
            scraped_at = datetime.now(timezone.utc)

            # Write to knowledge/raw/
            slug = url_to_slug(url)
            (KNOWLEDGE_RAW / f"{slug}.md").write_text(content, encoding="utf-8")

            # Insert into Snowflake
            cur.execute(INSERT_SQL, (url, source, content, scraped_at))
            conn.commit()
            loaded += 1
            print(f"  OK — {len(content)} chars")
        except Exception as exc:
            print(f"  SKIP — {exc}")

    cur.close()
    conn.close()
    print(f"\nDone — {loaded}/{len(TARGETS)} pages loaded to RAW.FIRECRAWL_PAGES and knowledge/raw/")
```

- [ ] **Step 3: Commit**

```bash
git add extract/load_firecrawl.py
git commit -m "feat: add Firecrawl extraction script"
```

---

### Task 7: Run load_firecrawl.py and verify data

**Files:** No changes — run and verify only.

- [ ] **Step 1: Run the script**

```bash
source .venv/bin/activate
python extract/load_firecrawl.py
```

Expected output (one line per URL):
```
Scraping https://skims.com/pages/our-story ...
  OK — 3241 chars
Scraping https://skims.com/collections/shapewear ...
  OK — 8102 chars
...
Done — N/7 pages loaded to RAW.FIRECRAWL_PAGES and knowledge/raw/
```

If a URL prints `SKIP`, check the error message. Common causes: rate limit (wait 10s and retry), URL has changed (find the current URL and update `TARGETS`), paywall (Firecrawl may still return partial content — check `content` length).

- [ ] **Step 2: Verify files in knowledge/raw/**

```bash
ls -lh knowledge/raw/
```

Expected: one `.md` file per successfully scraped URL (plus `.gitkeep`).

- [ ] **Step 3: Verify rows in Snowflake**

```sql
SELECT source_name, COUNT(*) AS pages, MIN(scraped_at) AS first_scraped
FROM RAW.FIRECRAWL_PAGES
GROUP BY source_name
ORDER BY source_name;
```

Expected: rows for each `source_name` with a recent `scraped_at`.

- [ ] **Step 4: Commit scraped knowledge/raw/ files**

```bash
git add knowledge/raw/
git commit -m "feat: add initial scraped sources to knowledge/raw"
```

---

### Task 8: Final cleanup commit

**Files:** No new changes — verify repo state and push.

- [ ] **Step 1: Confirm .env is not tracked**

```bash
git status
```

`.env` must NOT appear in the output. If it does: `git rm --cached .env` immediately.

- [ ] **Step 2: Verify both raw tables exist and have data**

```sql
SELECT 'census' AS src, COUNT(*) FROM RAW.CENSUS_RETAIL_SALES
UNION ALL
SELECT 'firecrawl', COUNT(*) FROM RAW.FIRECRAWL_PAGES;
```

Expected: two rows, both with count > 0.

- [ ] **Step 3: Final commit**

```bash
git status   # should be clean or only knowledge/raw/ files
git push origin main
```
