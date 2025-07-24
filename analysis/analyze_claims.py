# analysis/analyze_claims.py

import pandas as pd
import mysql.connector
from config.db_config import DB_CONFIG

def fetch_claims_data():
    """Fetch relevant claims data from the database."""
    conn = mysql.connector.connect(**DB_CONFIG)
    query = """
        SELECT 
            icd9_diagnosis_code,
            hcpcs_code,
            medicare_payment,
            patient_deductible,
            coinsurance_amount
        FROM claims
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def analyze_costs(df):
    """Perform cost analysis on claims data."""
    df['patient_cost'] = df['patient_deductible'] + df['coinsurance_amount']

    print("\n🧾 Top 10 Average Medicare Payments by Diagnosis Code:")
    top_diagnoses = df.groupby('icd9_diagnosis_code')['medicare_payment'].mean()
    print(top_diagnoses.sort_values(ascending=False).head(10))

    print("\n💵 Medicare vs. Patient Cost Comparison:")
    avg_medicare = df['medicare_payment'].mean()
    avg_patient = df['patient_cost'].mean()
    total_avg = avg_medicare + avg_patient
    patient_ratio = (avg_patient / total_avg) if total_avg else 0

    print(f"Average Medicare Payment : ${avg_medicare:.2f}")
    print(f"Average Patient Cost     : ${avg_patient:.2f}")
    print(f"Patient Cost Share       : {patient_ratio:.2%}")

if __name__ == "__main__":
    claims_df = fetch_claims_data()
    analyze_costs(claims_df)
