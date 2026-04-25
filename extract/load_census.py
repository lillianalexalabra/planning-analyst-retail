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
    try:
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
        placeholders = ", ".join(["(%s, %s, %s, %s, %s, %s, %s)"] * len(values))
        cur.execute(
            f"INSERT INTO RAW.CENSUS_RETAIL_SALES "
            f"(cell_value, error_data, time_slot_id, seasonally_adj, "
            f"category_code, data_type_code, geo_level) VALUES {placeholders}",
            [v for row in values for v in row],
        )
        conn.commit()
        return len(values)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("Fetching Census MRTS data (2019-present)...")
    rows = fetch_census()
    print(f"Fetched {len(rows)} rows from Census API")
    if not rows:
        print("No rows returned from Census API — aborting to protect existing data.")
        raise SystemExit(1)
    print("Loading to Snowflake RAW.CENSUS_RETAIL_SALES...")
    count = load(rows)
    print(f"Done — {count} rows loaded")
