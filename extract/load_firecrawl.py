# extract/load_firecrawl.py
from pathlib import Path
from dotenv import load_dotenv
import os
import re
from datetime import datetime, timezone
import snowflake.connector
from firecrawl import V1FirecrawlApp

load_dotenv(Path(__file__).parent.parent / ".env")

TARGETS = [
    # existing sources
    {"url": "https://skims.com/pages/our-story",               "source_name": "skims"},
    {"url": "https://skims.com/collections/shapewear",          "source_name": "skims"},
    {"url": "https://skims.com/collections/bras-and-underwear", "source_name": "skims"},
    {"url": "https://www.businessoffashion.com/tags/skims",     "source_name": "businessoffashion"},
    {"url": "https://www.voguebusiness.com/t/skims",            "source_name": "voguebusiness"},
    {"url": "https://nrf.com/research/annual-retail-and-food-services-sales", "source_name": "nrf"},
    {"url": "https://nrf.com/research/monthly-retail-trade",    "source_name": "nrf"},
    # new sources
    {"url": "https://en.wikipedia.org/wiki/Skims",              "source_name": "wikipedia"},
    {"url": "https://en.wikipedia.org/wiki/Spanx",              "source_name": "wikipedia"},
    {"url": "https://en.wikipedia.org/wiki/Kim_Kardashian",     "source_name": "wikipedia"},
    {"url": "https://en.wikipedia.org/wiki/Shapewear",          "source_name": "wikipedia"},
    {"url": "https://skims.com/collections/loungewear",         "source_name": "skims"},
    {"url": "https://skims.com/collections/swim",               "source_name": "skims"},
    {"url": "https://skims.com/collections/home",               "source_name": "skims"},
    {"url": "https://nrf.com/topics/holiday-and-seasonal-trends", "source_name": "nrf"},
    {"url": "https://www.retaildive.com/tag/apparel/",          "source_name": "retaildive"},
    {"url": "https://www.glossy.co/tag/skims/",                 "source_name": "glossy"},
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


def scrape(app: V1FirecrawlApp, url: str) -> str:
    result = app.scrape_url(url, formats=["markdown"])
    if hasattr(result, "markdown") and result.markdown:
        return result.markdown
    if isinstance(result, dict):
        return result.get("markdown") or result.get("content") or ""
    raise ValueError(f"Unexpected scrape result type: {type(result)}")


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
    app = V1FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])
    conn = get_conn()
    cur = None
    try:
        cur = conn.cursor()
        cur.execute("CREATE SCHEMA IF NOT EXISTS RAW")
        cur.execute(CREATE_TABLE)

        loaded = 0
        for target in TARGETS:
            url, source = target["url"], target["source_name"]
            print(f"Scraping {url} ...")
            try:
                content = scrape(app, url)
                if not content:
                    print(f"  SKIP — empty content returned")
                    continue
                scraped_at = datetime.now(timezone.utc)

                # Insert into Snowflake first (durable record before file write)
                cur.execute(INSERT_SQL, (url, source, content, scraped_at))
                conn.commit()

                # Write to knowledge/raw/ after Snowflake commit
                slug = url_to_slug(url)
                (KNOWLEDGE_RAW / f"{slug}.md").write_text(content, encoding="utf-8")

                loaded += 1
                print(f"  OK — {len(content)} chars")
            except Exception as exc:
                print(f"  SKIP — {exc}")

        print(f"\nDone — {loaded}/{len(TARGETS)} pages loaded to RAW.FIRECRAWL_PAGES and knowledge/raw/")
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        conn.close()
