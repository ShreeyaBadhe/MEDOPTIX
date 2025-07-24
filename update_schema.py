import mysql.connector
from config.db_config import DB_CONFIG

ALTER_QUERY = """
ALTER TABLE beneficiary_info
ADD COLUMN SP_ALZHDMTA TINYINT,
ADD COLUMN SP_CHF TINYINT,
ADD COLUMN SP_CHRNKIDN TINYINT,
ADD COLUMN SP_CNCR TINYINT,
ADD COLUMN SP_COPD TINYINT,
ADD COLUMN SP_DEPRESSN TINYINT,
ADD COLUMN SP_DIABETES TINYINT,
ADD COLUMN SP_ISCHMCHT TINYINT,
ADD COLUMN SP_OSTEOPRS TINYINT,
ADD COLUMN SP_RA_OA TINYINT,
ADD COLUMN SP_STRKETIA TINYINT;
"""

try:
    print("🔌 Connecting to MySQL...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(ALTER_QUERY)
    conn.commit()
    print("✅ Schema updated: Chronic condition columns added to `beneficiary_info`.")
except mysql.connector.Error as err:
    if err.errno == 1060:
        print("⚠️ Columns already exist. Nothing changed.")
    else:
        print(f"❌ Error: {err}")
finally:
    cursor.close()
    conn.close()
    print("🔒 Connection closed.")
