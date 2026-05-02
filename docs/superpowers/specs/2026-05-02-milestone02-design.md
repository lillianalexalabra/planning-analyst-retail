# Milestone 02 Design — Transform, Present & Polish

**Date:** 2026-05-02
**Project:** Planning Analyst Retail (SKIMS Market)
**Course:** ISBA 4715

---

## Scope

Complete all remaining Milestone 02 deliverables:

1. Streamlit dashboard (deployed to Streamlit Community Cloud)
2. Knowledge base expansion (15+ raw sources, 3 wiki pages, index.md)
3. ERD added to README
4. Firecrawl added to GitHub Actions pipeline
5. Repo cleanup (.gitignore, untracked files committed)

The dbt project and Census pipeline are already complete from prior work.

---

## 1. Streamlit Dashboard

### Files

```
dashboard/
├── app.py
└── requirements.txt
```

### Architecture

Single-page app with a sidebar and three tabs. Connects to Snowflake mart tables using `snowflake-connector-python`. Credentials loaded from `st.secrets` (matches `.env` variable names: `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_ROLE`).

### Sidebar

- **Category multi-select** — filters by `dim_category.category_code` / display name
- **Year range slider** — filters `fact_retail_sales.period` by year

### Tab 1 — Overview (Descriptive: "What happened?")

- Three KPI metric cards: latest month sales ($M), MoM % change, YoY % change
- Line chart: monthly sales over time, one line per selected category
- Answers: how has retail sales in apparel/intimates trended?

### Tab 2 — Seasonal Patterns (Diagnostic: "Why did it happen?")

- Bar chart: average sales by calendar month (Jan–Dec), averaged across all years
- Highlights which months consistently peak — directly answers the seasonal demand question for shapewear/intimates
- Answers: which months drive demand, and why does inventory need to be positioned earlier?

### Tab 3 — Inventory Implications (Diagnostic: "What does this mean?")

- Line chart: YoY % change over time to show acceleration/deceleration
- Summary table: peak months, trough months, average Q4 uplift vs. annual average
- Framing text tying insights to inventory positioning language relevant to a Planning Analyst

### Dependencies (`dashboard/requirements.txt`)

```
streamlit
snowflake-connector-python
pandas
plotly
```

### Deployment

Deploy to Streamlit Community Cloud:
- Repo: `lillianalexalabra/planning-analyst-retail`
- Branch: `main`
- Main file: `dashboard/app.py`
- Secrets: add Snowflake credentials in App Settings → Secrets (TOML format)

---

## 2. Knowledge Base

### Raw Sources (target: 17+ total, currently 7)

Scrape ~10 additional URLs using existing `load_firecrawl.py`. Target sites:

- **SKIMS** (skims.com): additional pages (press, sustainability, sizing)
- **Business of Fashion** (businessoffashion.com): specific SKIMS articles
- **Vogue Business** (voguebusiness.com): additional SKIMS/shapewear articles
- **Retail Dive or Glossy** (retaildive.com or glossy.co): shapewear/intimates market coverage
- **NRF** (nrf.com): additional retail reports

All scraped files saved to `knowledge/raw/` as markdown, named by URL slug.

### Wiki Pages (3 generated, saved to `knowledge/wiki/`)

- **`overview.md`** — SKIMS company profile: founding story, founding team, valuation, product lines, brand positioning, key milestones
- **`market-landscape.md`** — competitive positioning, comparable brands (Spanx, Savage X Fenty, Skintimate), market size and growth, distribution strategy
- **`demand-drivers.md`** — seasonal demand patterns in shapewear/intimates, Q4 and holiday dynamics, inventory challenges, demand signals

Each wiki page synthesizes across multiple raw sources. Not single-source summaries.

### Index

`knowledge/index.md` — lists all wiki pages with one-line summaries. Format:

```markdown
# Knowledge Base Index

## Wiki Pages
- [overview.md](wiki/overview.md) — SKIMS company profile, founding, and brand positioning
- [market-landscape.md](wiki/market-landscape.md) — Competitive landscape and market sizing
- [demand-drivers.md](wiki/demand-drivers.md) — Seasonal demand patterns and inventory implications

## Raw Sources
One entry per file in `knowledge/raw/`, with the URL it was scraped from as the description.
```

---

## 3. ERD

Generate a Mermaid ERD from the dbt mart models and insert it into `README.md` replacing the "Coming in Milestone 02" placeholder.

Tables and relationships:

```
fact_retail_sales }o--|| dim_date      : period
fact_retail_sales }o--|| dim_category  : category_code
fact_retail_sales }o--|| dim_region    : region_code
```

Include all columns for each table.

---

## 4. GitHub Actions Pipeline Update

Add a Firecrawl step to `.github/workflows/pipeline.yml`:

- Add `FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}` to the `env` block
- Add step after Census load: `python extract/load_firecrawl.py`
- User must manually add `FIRECRAWL_API_KEY` to GitHub repo secrets

---

## 5. Repo Cleanup

- Add `dbt/.user.yml` to `.gitignore`
- Add `dbt/logs/` to `.gitignore`
- Commit the previously untracked `docs/superpowers/plans/2026-04-25-dbt-github-actions.md`
- Verify no credentials or scratch files are tracked

---

## Out of Scope

- Presentation slides (PDF) — user creates independently and submits to Brightspace
- Streamlit Community Cloud account setup — user completes manually after `dashboard/app.py` is pushed
