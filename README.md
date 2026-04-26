# Retail Planning Analytics — SKIMS Market

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

_Coming in Milestone 02._

## ERD

_Coming in Milestone 02 after dbt star schema is built._

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
| Milestone 02: Transform, Dashboard & Knowledge Base | 🔲 In progress |
| Final Submission | 🔲 Pending |
