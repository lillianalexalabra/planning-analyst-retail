---
title: Project Proposal Design
date: 2026-04-11
topic: proposal
---

# Project Proposal Design

## Job Posting

**Role:** Planning Analyst  
**Company:** SKIMS  
**Location:** Los Angeles, CA  
**Salary:** $75,000–$85,000/year  
**SQL requirement:** "Proficiency in data analysis tools and software, such as Excel, SQL, and forecasting software (e.g., SAP, Oracle, or similar)"

## Project Framing

**Core business question:** How does seasonal demand in the shapewear, loungewear, and intimates category behave — and what does it mean for inventory positioning?

**Descriptive analytics:** What have apparel/intimates sales looked like over time? What are the peak seasons, category trends, and YoY growth patterns in SKIMS's market?

**Diagnostic analytics:** Why do demand spikes happen when they do? What seasonal signals predict overstock/understock risk in this category?

**Transferability:** Transfers to any retail planning, merchandising, or supply chain analyst role (Target, Revolve, Nordstrom, etc.)

## Data Sources

### Source 1 — US Census Bureau Monthly Retail Trade API
- Monthly retail sales by NAICS category (clothing & accessories, general merchandise)
- Free, no API key required
- Scheduled via GitHub Actions
- Loads into Snowflake raw schema

### Source 2 — Web Scrape (Knowledge Base)
- SKIMS.com brand pages and product categories
- Business of Fashion, Vogue Business, WWD market trend articles
- NRF (National Retail Federation) industry reports
- Comparable brand coverage (Hanesbrands, Victoria's Secret investor docs)
- Target: 15+ sources across 3+ sites → `knowledge/raw/`

## Star Schema

```
fact_retail_sales
├── date_key        → dim_date     (year, month, quarter, season)
├── category_key    → dim_category (NAICS code, name, subcategory)
├── region_key      → dim_region   (US national + regional)
└── measures: sales_millions, month_over_month_change, year_over_year_change
```

### dbt Layers
- `stg_census_retail` — clean, rename, cast types
- `dim_date`, `dim_category`, `dim_region` — dimension tables
- `fact_retail_sales` — joined fact table with calculated fields

## Streamlit Dashboard

- **Tab 1 — Demand Overview (Descriptive):** Time-series of apparel/intimates sales by month/quarter. Filters: date range, category. Callouts: peak season, YoY growth.
- **Tab 2 — Seasonality & Risk (Diagnostic):** Season-over-season comparison, demand volatility by category, overstock/understock risk signals.
- **Interactive elements:** Date range selector, category filter, season toggle

## Knowledge Base

```
knowledge/
├── raw/         # 15+ scraped sources
├── wiki/
│   ├── overview.md           # SKIMS brand, market position, product lines
│   ├── market-landscape.md   # shapewear/intimates category size, growth, competitors
│   └── planning-themes.md    # demand patterns, seasonality, inventory challenges
└── index.md    # all wiki pages with one-line summaries
```

## Repo Structure

```
planning-analyst-retail/
├── .gitignore
├── CLAUDE.md
├── docs/
│   ├── job-posting.pdf
│   └── proposal.md
├── knowledge/
│   ├── raw/
│   └── wiki/
├── extract/       # Python extraction scripts
├── dbt/           # dbt project
└── dashboard/     # Streamlit app
```

## User Skills Highlighted
- SQL — inventory/sales analysis, star schema queries
- Python — data extraction pipeline, Census API ingestion
- Dashboards — Streamlit KPI reporting to leadership
- Excel — baseline skill the posting explicitly requires
