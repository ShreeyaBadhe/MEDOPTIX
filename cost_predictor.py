import pandas as pd
import mysql.connector
from config.db_config import DB_CONFIG
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor
import matplotlib.pyplot as plt
import joblib

# --- Load Data from MySQL ---
conn = mysql.connector.connect(**DB_CONFIG)
df_claims = pd.read_sql("SELECT * FROM claims c JOIN beneficiary_info b ON c.bene_id = b.bene_id", conn)
conn.close()

# --- Feature Engineering ---
df_claims['age'] = 2022 - pd.to_datetime(df_claims['birth_date']).dt.year
chronic_cols = [col for col in df_claims.columns if col.startswith("SP_")]

# Drop rows with missing target
df_claims = df_claims.dropna(subset=['medicare_payment'])

# --- Prepare Features and Target ---
X = df_claims[['age', 'icd9_diagnosis_code', 'hcpcs_code'] + chronic_cols].copy()
y = df_claims['medicare_payment']

# --- Encode Categorical Features ---
le_icd9 = LabelEncoder()
le_hcpcs = LabelEncoder()
X['icd9_diagnosis_code'] = le_icd9.fit_transform(X['icd9_diagnosis_code'].astype(str))
X['hcpcs_code'] = le_hcpcs.fit_transform(X['hcpcs_code'].astype(str))

# --- Train/Test Split ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- Train XGBoost Model ---
model = XGBRegressor(n_estimators=100, max_depth=6, random_state=42)
model.fit(X_train, y_train)

# --- Evaluate Model ---
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
print(f"MAE: {mae:.2f}")
print(f"R^2 Score: {r2:.2f}")

# --- Plot Actual vs Predicted ---
plt.figure(figsize=(8, 5))
plt.scatter(y_test, y_pred, alpha=0.4)
plt.xlabel("Actual Cost")
plt.ylabel("Predicted Cost")
plt.title("Actual vs Predicted Medicare Cost")
plt.grid(True)
plt.tight_layout()
plt.savefig("actual_vs_predicted.png")
print("📊 Saved plot as 'actual_vs_predicted.png'")

# --- Save Model and LabelEncoders ---
joblib.dump(model, "models/cost_model_xgb.joblib")
joblib.dump(le_icd9, "models/le_icd9.joblib")
joblib.dump(le_hcpcs, "models/le_hcpcs.joblib")
print("✅ Model and encoders saved.")
