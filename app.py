import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
import joblib
import os
import gdown
from datetime import date
from config.db_config import DB_CONFIG

# ------------------------------
# 🚀 Load data from MySQL
# ------------------------------
@st.cache_data
def load_data():
    conn = mysql.connector.connect(**DB_CONFIG)
    df_beneficiary = pd.read_sql("SELECT * FROM beneficiary_info", conn)
    df_claims = pd.read_sql("SELECT * FROM claims", conn)
    conn.close()
    return df_beneficiary, df_claims
GDRIVE_MODELS = {
    "cost_model_xgb": "https://drive.google.com/uc?id=1Z-3xB2tSRebrbgUjNO_68Bhiz9IiM1BD",
    "le_icd9": "https://drive.google.com/uc?id=1VlHsM0Q8Qc7-DlLJkaij5Pa9XfeMjFLD",
    "le_hcpcs": "https://drive.google.com/uc?id=16nYj5VHD2hqIM45GkeRV92zGYq2vtKge",
}
# ------------------------------
# 🧠 Load Model + Encoders
# ------------------------------
@st.cache_resource
def load_model_assets():
    os.makedirs("models", exist_ok=True)
    
    model_path = "models/cost_model_xgb.joblib"
    icd9_path = "models/le_icd9.joblib"
    hcpcs_path = "models/le_hcpcs.joblib"
    
    if not os.path.exists(model_path):
        gdown.download(GDRIVE_MODELS["cost_model_xgb"], model_path, quiet=False)
    if not os.path.exists(icd9_path):
        gdown.download(GDRIVE_MODELS["le_icd9"], icd9_path, quiet=False)
    if not os.path.exists(hcpcs_path):
        gdown.download(GDRIVE_MODELS["le_hcpcs"], hcpcs_path, quiet=False)

    model = joblib.load(model_path)
    le_icd9 = joblib.load(icd9_path)
    le_hcpcs = joblib.load(hcpcs_path)

    chronic_cols = [f for f in model.feature_names_in_ if f.startswith("SP_")]
    return model, le_icd9, le_hcpcs, chronic_cols

def encode_or_unknown(le, val):
    try:
        return int(le.transform([str(val)])[0])
    except:
        return -1

def build_feature_row(age, icd9, hcpcs, chronic_cols, selected_flags, le_icd9, le_hcpcs):
    row = {
        "age": age,
        "icd9_diagnosis_code": encode_or_unknown(le_icd9, icd9),
        "hcpcs_code": encode_or_unknown(le_hcpcs, hcpcs),
    }
    for col in chronic_cols:
        row[col] = 1 if col in selected_flags else 0
    return pd.DataFrame([row])

# ------------------------------
# 🎨 App Layout & Sidebar
# ------------------------------
st.set_page_config(page_title="MedOptix Dashboard", layout="wide")

try:
    st.sidebar.image("logo.png", use_container_width=True)
except:
    st.sidebar.warning("⚠️ Logo not found.")

st.sidebar.header("🔎 Filters")

# Load & merge data
df_beneficiary, df_claims = load_data()
df = pd.merge(df_claims, df_beneficiary, on="bene_id")

# ------------------------------
# 📌 Filters
# ------------------------------
df["age"] = pd.to_datetime("2022-01-01").year - pd.to_datetime(df["birth_date"], errors="coerce").dt.year
age_bins = [0, 65, 75, 85, 100, 120]
df["age_group"] = pd.cut(df["age"], bins=age_bins, labels=["<65", "65-74", "75-84", "85-99", "100+"])

state_filter = st.sidebar.selectbox("State", options=["All"] + sorted(df["state_code"].dropna().unique().tolist()))
age_filter = st.sidebar.selectbox("Age Group", options=["All"] + df["age_group"].dropna().astype(str).unique().tolist())

chronic_cols = [col for col in df.columns if col.startswith("SP_")]
chronic_filter = st.sidebar.selectbox("Chronic Condition", options=["All"] + chronic_cols)

if state_filter != "All":
    df = df[df["state_code"] == state_filter]
if age_filter != "All":
    df = df[df["age_group"] == age_filter]
if chronic_filter != "All":
    df = df[df[chronic_filter] == 1]

# ------------------------------
# 📊 Cost Summary
# ------------------------------
st.title("📊 Cost Summary Dashboard")

st.metric("💰 Total Medicare Payment", f"${df['medicare_payment'].sum():,.2f}")
st.metric("🧾 Total Patient Cost", f"${(df['patient_deductible'] + df['coinsurance_amount']).sum():,.2f}")

st.subheader("💡 Medicare Payments by Diagnosis Code")
top_diag = df.groupby("icd9_diagnosis_code")["medicare_payment"].sum().nlargest(10).reset_index()
fig_diag = px.bar(top_diag, x="icd9_diagnosis_code", y="medicare_payment", title="Top 10 Diagnosis Codes")
st.plotly_chart(fig_diag, use_container_width=True)

# ------------------------------
# 🧠 Chronic Insights
# ------------------------------
st.title("🧠 Chronic Condition Insights")

chronic_summary = {
    col: df[df[col] == 1]["medicare_payment"].sum()
    for col in chronic_cols
}
chronic_df = pd.DataFrame(list(chronic_summary.items()), columns=["Condition", "Total Medicare Cost"])
chronic_df = chronic_df[chronic_df["Total Medicare Cost"] > 0]

if not chronic_df.empty:
    fig_chronic = px.pie(chronic_df, names="Condition", values="Total Medicare Cost",
                         title="Medicare Cost by Chronic Condition")
    st.plotly_chart(fig_chronic, use_container_width=True)
else:
    st.info("No chronic condition costs found for current filters.")

# ------------------------------
# 🧾 Individual Claim Explorer
# ------------------------------
st.title("🧾 Individual Claim Explorer")

selected_id = st.selectbox("🔍 Select Beneficiary ID", options=sorted(df["bene_id"].unique()))
filtered_claims = df[df["bene_id"] == selected_id]

st.write(f"Showing {len(filtered_claims)} claim(s) for Beneficiary ID: `{selected_id}`")
st.dataframe(filtered_claims[[
    "claim_id", "bene_id", "birth_date", "state_code", "age", 
    "icd9_diagnosis_code", "hcpcs_code", 
    "medicare_payment", "patient_deductible", "coinsurance_amount"
]], use_container_width=True)

# ------------------------------
# 💸 Cost Predictor
# ------------------------------
st.title("💸 Medicare Cost Predictor")

model, le_icd9, le_hcpcs, chronic_flags = load_model_assets()

with st.form("predict_form"):
    birth_year = st.number_input("Birth Year", min_value=1900, max_value=date.today().year, value=1950)
    age = date.today().year - birth_year
    icd9 = st.text_input("ICD9 Diagnosis Code", value="")
    hcpcs = st.text_input("HCPCS Procedure Code", value="")
    selected_flags = st.multiselect("Select Chronic Conditions", chronic_flags)

    submitted = st.form_submit_button("Predict Cost")
    if submitted:
        X_pred = build_feature_row(age, icd9, hcpcs, chronic_flags, selected_flags, le_icd9, le_hcpcs)
        X_pred = X_pred.reindex(columns=model.feature_names_in_, fill_value=0)
        prediction = float(model.predict(X_pred)[0])
        st.metric("💵 Predicted Medicare Payment", f"${prediction:,.2f}")

# ------------------------------
# 📁 Batch Prediction from CSV
# ------------------------------
st.subheader("📂 Upload CSV for Batch Prediction")
csv_file = st.file_uploader("Upload CSV with columns: age, icd9_diagnosis_code, hcpcs_code, SP_*", type=["csv"])

if csv_file:
    df_upload = pd.read_csv(csv_file)
    df_upload["icd9_diagnosis_code"] = df_upload["icd9_diagnosis_code"].astype(str).apply(lambda v: encode_or_unknown(le_icd9, v))
    df_upload["hcpcs_code"] = df_upload["hcpcs_code"].astype(str).apply(lambda v: encode_or_unknown(le_hcpcs, v))

    missing = [col for col in model.feature_names_in_ if col not in df_upload.columns]
    for m in missing:
        df_upload[m] = 0
    df_upload = df_upload[model.feature_names_in_]

    preds = model.predict(df_upload)
    df_out = df_upload.copy()
    df_out["predicted_medicare_payment"] = preds
    st.dataframe(df_out.head())
    st.download_button("⬇️ Download Predictions", df_out.to_csv(index=False), "predictions.csv", "text/csv")

# ------------------------------
# 📂 Download Filtered Data
# ------------------------------
st.download_button(
    label="⬇️ Download All Filtered Data as CSV",
    data=df.to_csv(index=False),
    file_name="filtered_claims.csv",
    mime="text/csv"
)
