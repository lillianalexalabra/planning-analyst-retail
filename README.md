# Retail Planning Analytics — SKIMS Market

**Live dashboard:** https://planning-analyst-retail-e5aljtcqwdy3appczhunata.streamlit.app

End-to-end analytics pipeline targeting the **Planning Analyst** role at SKIMS. Pulls US retail sales data from the Census Bureau API, scrapes industry sources via Firecrawl, loads both into Snowflake, transforms through a dbt star schema, and surfaces seasonal demand insights in a Streamlit dashboard.

**Core business question:** How does seasonal demand in the shapewear, loungewear, and intimates category behave — and what does that mean for inventory positioning?

---

## Tech Stack

| Layer | Tool |
|---|---|
| Data Warehouse | Snowflake |
| Transformation | dbt |
| Orchestration | GitHub Actions |
| Dashboard | Streamlit |
| Web Scraping | Firecrawl |
| Language | Python, SQL |

---

## Data Sources

| # | Source | Type | Target |
|---|---|---|---|
| 1 | US Census Bureau Monthly Retail Trade Survey (MRTS) | REST API | `RAW.CENSUS_RETAIL_SALES` |
| 2 | SKIMS, Business of Fashion, Vogue Business, NRF | Web scrape (Firecrawl) | `RAW.FIRECRAWL_PAGES` + `knowledge/raw/` |

---

## Repo Structure

```
planning-analyst-retail/
├── extract/
│   ├── load_census.py        # Census MRTS API → Snowflake RAW
│   ├── load_firecrawl.py     # Firecrawl scrape → Snowflake RAW + knowledge/raw/
│   ├── requirements.txt
│   └── .env.example
├── dbt/                      # dbt project (staging + mart models)
├── dashboard/                # Streamlit app
├── knowledge/
│   ├── raw/                  # Scraped source files (markdown)
│   └── wiki/                 # Claude Code-generated synthesis pages
└── docs/
    ├── proposal.md
    └── job-posting.pdf
```

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/lillianalexalabra/planning-analyst-retail.git
cd planning-analyst-retail
python3 -m venv .venv
source .venv/bin/activate
pip install -r extract/requirements.txt
```

### 2. Configure credentials

Copy `.env.example` to `.env` at the project root and fill in your values:

```bash
cp extract/.env.example .env
```

Required variables:

```
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_PASSWORD=
SNOWFLAKE_DATABASE=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_ROLE=
FIRECRAWL_API_KEY=
```

### 3. Run extraction scripts

```bash
# Load Census MRTS data into Snowflake RAW
python extract/load_census.py

# Scrape web sources into Snowflake RAW + knowledge/raw/
python extract/load_firecrawl.py
```

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

---

## Snowflake Schema (RAW Layer)

**`RAW.CENSUS_RETAIL_SALES`** — US monthly retail sales from Census MRTS API (2019–present)

| Column | Description |
|---|---|
| `cell_value` | Sales figure |
| `time_slot_id` | Period (YYYY-MM) |
| `category_code` | NAICS-based retail category |
| `data_type_code` | Measure type (SM = sales in $M) |
| `seasonally_adj` | Whether seasonally adjusted |
| `error_data` | Margin of error |
| `geo_level` | Geography (US) |
| `_loaded_at` | Ingestion timestamp |

**`RAW.FIRECRAWL_PAGES`** — Scraped web content

| Column | Description |
|---|---|
| `url` | Source URL |
| `source_name` | Publication (skims, businessoffashion, nrf, etc.) |
| `content` | Full markdown text |
| `scraped_at` | When Firecrawl fetched it |
| `_loaded_at` | Ingestion timestamp |

---

## Pipeline Diagram

```mermaid
flowchart TB
    subgraph src1 [Source 1 — Structured Data]
        A["Census Bureau MRTS API\n(no auth required)"]
    end

    subgraph src2 [Source 2 — Knowledge Base]
        B["Web Sources\n(SKIMS, BoF, Vogue Business, NRF)"]
    end

    subgraph extract [Extract & Load — extract/]
        C["load_census.py"]
        D["load_firecrawl.py"]
    end

    subgraph raw [Snowflake — RAW Schema]
        E["RAW.CENSUS_RETAIL_SALES"]
        F["RAW.FIRECRAWL_PAGES"]
    end

    subgraph kb [Knowledge Base — knowledge/]
        G["knowledge/raw/\n(scraped markdown files)"]
        H["knowledge/wiki/\n(Claude Code synthesis)"]
    end

    subgraph dbt [dbt — Transformation]
        I["stg_census_retail\n(staging)"]
        J["dim_date · dim_category · dim_region\nfact_retail_sales\n(mart / star schema)"]
    end

    subgraph output [Output]
        K["Streamlit Dashboard\n(deployed)"]
        L["Claude Code\n(knowledge base queries)"]
    end

    A --> C --> E --> I --> J --> K
    B --> D --> F
    D --> G --> H --> L
```

## ERD

```mermaid
erDiagram
    FACT_RETAIL_SALES {
        varchar PERIOD FK
        varchar CATEGORY_CODE FK
        varchar REGION_CODE FK
        varchar DATA_TYPE_CODE
        varchar SEASONALLY_ADJ
        float   SALES_MILLIONS
        float   MONTH_OVER_MONTH_PCT
        float   YEAR_OVER_YEAR_PCT
    }
    DIM_DATE {
        varchar PERIOD PK
        int     YEAR
        int     MONTH
        int     QUARTER
        varchar SEASON
    }
    DIM_CATEGORY {
        varchar CATEGORY_CODE PK
        varchar CATEGORY_NAME
    }
    DIM_REGION {
        varchar REGION_CODE PK
        varchar REGION_NAME
        varchar REGION_TYPE
    }
    FACT_RETAIL_SALES }o--|| DIM_DATE     : "period"
    FACT_RETAIL_SALES }o--|| DIM_CATEGORY : "category_code"
    FACT_RETAIL_SALES }o--|| DIM_REGION   : "region_code"
```

---

## Insights Summary

Analysis of US Census Bureau Monthly Retail Trade Survey data (NAICS 448 — Clothing and Clothing Accessories Stores, 2019–2026) surfaces three planning-relevant findings:

**1. Q4 holiday gifting drives a 24.5% demand surge — and December is the crown of that season.**
October–December averages $7.2B/month vs. the $5.8B annual monthly average (+24.5%). December alone reaches $9.3B — 60% above a typical month and the single largest month in the calendar. The entire Q4 window requires inventory to be in place before demand peaks.

**2. Demand falls 54% from December to January — the steepest drop in the calendar.**
January averages $4.4B, down from December's $9.3B peak. This makes January the natural markdown and clearance window. Inventory not cleared before January faces the worst sell-through environment of the year.

**3. Recommendation: Commit to purchase orders by October 15.**
With a 6–8 week apparel lead time (production + ocean freight + domestic distribution), holiday inventory must be ordered by mid-October to land in the warehouse before the November/December demand peak. By the time December arrives, it is already too late to reorder.

---

## Knowledge Base

The `knowledge/` folder is a queryable knowledge base about SKIMS's market. Run Claude Code against this repo and ask questions like:

- "What does my knowledge base say about SKIMS's competitive position?"
- "What are the key demand drivers for shapewear?"
- "What inventory challenges does the fashion industry face heading into Q4?"

See `CLAUDE.md` for query conventions.

---

## Status

| Milestone | Status |
|---|---|
| Proposal | ✅ Complete |
| Milestone 01: Extract & Load | ✅ Complete |
| Milestone 02: Transform, Dashboard & Knowledge Base | ✅ Complete |
| Final Submission | 🔲 Pending |
