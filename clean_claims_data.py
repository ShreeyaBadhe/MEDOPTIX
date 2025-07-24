import pandas as pd
import mysql.connector
from config.db_config import DB_CONFIG
from pandas.api.types import is_numeric_dtype
from tqdm import tqdm

# --- Helper: Convert all values to native Python types ---
def convert_value(val):
    import numpy as np
    if pd.isnull(val):
        return None
    if isinstance(val, (np.int64, np.int32)):
        return int(val)
    if isinstance(val, (np.float64, np.float32)):
        return float(val)
    if isinstance(val, pd.Timestamp):
        return val.date()
    return str(val)

# --- Load the CSV ---
df = pd.read_csv("data/medicare_claims.csv")

# ===============================
# 🧾 Clean Beneficiary Info Table
# ===============================
beneficiary_df = df[[  
    'DESYNPUF_ID', 'BENE_BIRTH_DT', 'BENE_DEATH_DT',
    'BENE_SEX_IDENT_CD', 'BENE_RACE_CD', 'BENE_ESRD_IND',
    'SP_STATE_CODE', 'BENE_COUNTY_CD',
    'BENE_HI_CVRAGE_TOT_MONS', 'BENE_SMI_CVRAGE_TOT_MONS', 'BENE_HMO_CVRAGE_TOT_MONS',
    'SP_ALZHDMTA', 'SP_CHF', 'SP_CHRNKIDN', 'SP_CNCR', 'SP_COPD',
    'SP_DEPRESSN', 'SP_DIABETES', 'SP_ISCHMCHT', 'SP_OSTEOPRS', 'SP_RA_OA', 'SP_STRKETIA'
]].copy()

beneficiary_df.columns = [
    'bene_id', 'birth_date', 'death_date', 'sex_code', 'race_code',
    'esrd_ind', 'state_code', 'county_code', 'hi_coverage_mos',
    'smi_coverage_mos', 'hmo_coverage_mos',
    'SP_ALZHDMTA', 'SP_CHF', 'SP_CHRNKIDN', 'SP_CNCR', 'SP_COPD',
    'SP_DEPRESSN', 'SP_DIABETES', 'SP_ISCHMCHT', 'SP_OSTEOPRS', 'SP_RA_OA', 'SP_STRKETIA'
]

# Format date fields
beneficiary_df['birth_date'] = pd.to_datetime(beneficiary_df['birth_date'], format='%Y%m%d', errors='coerce').dt.date
beneficiary_df['death_date'] = pd.to_datetime(beneficiary_df['death_date'], format='%Y%m%d', errors='coerce').dt.date

# Handle numeric columns
int_columns = ['race_code', 'state_code', 'county_code', 'hi_coverage_mos', 'smi_coverage_mos', 'hmo_coverage_mos'] + \
              ['SP_ALZHDMTA', 'SP_CHF', 'SP_CHRNKIDN', 'SP_CNCR', 'SP_COPD',
               'SP_DEPRESSN', 'SP_DIABETES', 'SP_ISCHMCHT', 'SP_OSTEOPRS', 'SP_RA_OA', 'SP_STRKETIA']
for col in int_columns:
    if is_numeric_dtype(beneficiary_df[col]):
        beneficiary_df[col] = beneficiary_df[col].fillna(0).round().astype("Int64")

beneficiary_df['sex_code'] = beneficiary_df['sex_code'].astype(str)
beneficiary_df['esrd_ind'] = beneficiary_df['esrd_ind'].astype(str)

# Drop missing and duplicate bene_id
beneficiary_df.dropna(subset=['bene_id'], inplace=True)
beneficiary_df.drop_duplicates(subset=['bene_id'], inplace=True)

# ============================
# 💸 Clean Claims Table
# ============================
claims_df = df[[  
    'CLM_ID', 'DESYNPUF_ID', 'CLM_FROM_DT', 'CLM_THRU_DT',
    'ICD9_DGNS_CD_1', 'HCPCS_CD_1',
    'LINE_NCH_PMT_AMT_1', 'LINE_BENE_PTB_DDCTBL_AMT_1', 'LINE_COINSRNC_AMT_1'
]].copy()

claims_df.columns = [
    'claim_id', 'bene_id', 'claim_from', 'claim_thru',
    'icd9_diagnosis_code', 'hcpcs_code',
    'medicare_payment', 'patient_deductible', 'coinsurance_amount'
]

# Date formatting
claims_df['claim_from'] = pd.to_datetime(claims_df['claim_from'], format='%Y%m%d', errors='coerce').dt.date
claims_df['claim_thru'] = pd.to_datetime(claims_df['claim_thru'], format='%Y%m%d', errors='coerce').dt.date

claims_df.dropna(subset=['claim_id', 'bene_id'], inplace=True)
claims_df.drop_duplicates(subset=['claim_id'], inplace=True)

# Match bene_id to valid ones only
claims_df = claims_df[claims_df['bene_id'].isin(set(beneficiary_df['bene_id']))]
# ⏱️ TEMP: Limit to 10 rows for faster testing


# ================================
# 🗃️ Insert Data into MySQL Tables
# ================================
def insert_to_mysql(df, table_name, key_col):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    for _, row in tqdm(df.iterrows(), total=len(df), desc=f"Inserting into {table_name}"):
        placeholders = ', '.join(['%s'] * len(row))
        columns = ', '.join(row.index)
        sql = f"INSERT IGNORE INTO {table_name} ({columns}) VALUES ({placeholders})"
        try:
            values = [convert_value(v) for v in row]
            cursor.execute(sql, values)
        except mysql.connector.Error as err:
            print(f"❌ Error inserting into `{table_name}`: {err}")
            continue

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Done inserting into `{table_name}`.\n")

# Run Inserts
print("📤 Loading data into MySQL...")
insert_to_mysql(beneficiary_df, 'beneficiary_info', 'bene_id')
insert_to_mysql(claims_df, 'claims', 'claim_id')
print("🎉 All done!")
