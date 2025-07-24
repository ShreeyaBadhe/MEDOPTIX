# analysis/chronic_analysis.py

import pandas as pd
import mysql.connector
from config.db_config import DB_CONFIG

def fetch_data():
    """Fetch chronic condition indicators and cost-related fields from the database."""
    conn = mysql.connector.connect(**DB_CONFIG)
    query = """
        SELECT 
            b.bene_id,
            SP_ALZHDMTA, SP_CHF, SP_CHRNKIDN, SP_CNCR, SP_COPD,
            SP_DEPRESSN, SP_DIABETES, SP_ISCHMCHT, SP_OSTEOPRS, SP_RA_OA, SP_STRKETIA,
            c.medicare_payment, c.patient_deductible, c.coinsurance_amount
        FROM beneficiary_info b
        JOIN claims c ON b.bene_id = c.bene_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def analyze_chronic_costs(df):
    """Analyze total cost per chronic condition and identify high-risk patients."""
    df['total_cost'] = df['medicare_payment'] + df['patient_deductible'] + df['coinsurance_amount']
    chronic_cols = [col for col in df.columns if col.startswith('SP_')]

    print("\n📊 Total Cost per Chronic Condition:")
    for condition in chronic_cols:
        cost = df[df[condition] == 1]['total_cost'].sum()
        print(f"{condition: <15}: ${cost:,.2f}")

    print("\n🔥 High-Risk Patients (3+ chronic conditions):")
    df['condition_count'] = df[chronic_cols].sum(axis=1)
    high_risk_df = df[df['condition_count'] >= 3]
    avg_high_risk_cost = high_risk_df['total_cost'].mean()
    print(f"Avg total cost for high-risk patients: ${avg_high_risk_cost:,.2f}")
    print(f"Number of high-risk patients        : {len(high_risk_df)}")

if __name__ == "__main__":
    df = fetch_data()
    analyze_chronic_costs(df)
