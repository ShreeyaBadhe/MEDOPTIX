#!/usr/bin/env python
"""
Migrate data from Docker MySQL to AWS RDS MySQL
"""

import math
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

# Configuration
SRC_DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "medoptix_user",
    "password": "medoptix_pass",
    "database": "medoptix_db"
}

DST_DB_CONFIG = {
    "host": "medoptix-db.c1a6ekqqiek6.us-east-2.rds.amazonaws.com",
    "port": 3306,
    "user": "shreeyabadhe",
    "password": "Shreeya1124",  # 🔐 change in prod
    "database": "medoptix_db"
}

TABLES_TO_MIGRATE = ["beneficiary_info", "claims"]
READ_CHUNK = 100_000
WRITE_CHUNK = 2000

def get_engine(config: dict):
    url = URL.create(
        drivername="mysql+pymysql",
        username=config["user"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
        database=config["database"],
    )
    return create_engine(url, pool_pre_ping=True)

src_engine = get_engine(SRC_DB_CONFIG)
dst_engine = get_engine(DST_DB_CONFIG)

# 🔧 One-time: Create table with PRIMARY KEY in RDS
def create_beneficiary_info_schema():
    ddl = """
    CREATE TABLE IF NOT EXISTS beneficiary_info (
        bene_id VARCHAR(50) PRIMARY KEY,
        birth_date DATE,
        death_date VARCHAR(20),
        sex_code VARCHAR(10),
        race_code BIGINT,
        esrd_ind VARCHAR(10),
        state_code BIGINT,
        county_code BIGINT,
        hi_coverage_mos BIGINT,
        smi_coverage_mos BIGINT,
        hmo_coverage_mos BIGINT,
        SP_ALZHDMTA BIGINT,
        SP_CHF BIGINT,
        SP_CHRNKIDN BIGINT,
        SP_CNCR BIGINT,
        SP_COPD BIGINT,
        SP_DEPRESSN BIGINT,
        SP_DIABETES BIGINT,
        SP_ISCHMCHT BIGINT,
        SP_OSTEOPRS BIGINT,
        SP_RA_OA BIGINT,
        SP_STRKETIA BIGINT
    );
    """
    with dst_engine.begin() as conn:
        conn.execute(text(ddl))
    print("✅ Created `beneficiary_info` table with PK")

# 🛠 Migration
def migrate_table(table: str):
    print(f"\n🔄 Migrating `{table}`...")
    with src_engine.connect() as conn:
        total_rows = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()

    if total_rows == 0:
        print(f"⚠️  No rows in `{table}`")
        return

    offset = 0
    total_chunks = math.ceil(total_rows / READ_CHUNK)
    print(f"→ {total_rows:,} rows to migrate in {total_chunks} chunks")

    while offset < total_rows:
        print(f"   📥 Reading rows {offset} to {offset + READ_CHUNK - 1}")
        query = text(f"SELECT * FROM {table} LIMIT :limit OFFSET :offset")
        with src_engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"limit": READ_CHUNK, "offset": offset})

        if df.empty:
            break

        try:
            with dst_engine.begin() as conn:
                df.to_sql(
                    name=table,
                    con=conn,
                    if_exists="append",
                    index=False,
                    chunksize=WRITE_CHUNK,
                    method="multi"
                )
            print(f"   ✅ {len(df)} rows written to `{table}`")
        except SQLAlchemyError as err:
            print(f"   ❌ Write error: {err}")
            raise

        offset += READ_CHUNK

    print(f"✅ Migration done for `{table}`")

# 🔁 Main
def main():
    try:
        with src_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("🟢 Connected to Docker MySQL")
    except Exception as e:
        print("🔴 Docker DB error:", e)
        return

    try:
        with dst_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("🟢 Connected to AWS RDS MySQL")
    except Exception as e:
        print("🔴 RDS DB error:", e)
        return

    if "beneficiary_info" in TABLES_TO_MIGRATE:
        create_beneficiary_info_schema()

    for table in TABLES_TO_MIGRATE:
        migrate_table(table)

    print("\n🎉 All migrations complete")

if __name__ == "__main__":
    main()
