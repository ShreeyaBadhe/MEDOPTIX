# MedOptix: Medicare Claims analysis and Cost estimator

A lightweight open-source Streamlit app that visualizes and predicts Medicare claims cost using beneficiary and claims data. Ideal for healthcare analysts and researchers.

## 📽️ Demo Video

Watch the walkthrough here: [MedOptix Demo](https://drive.google.com/file/d/11P_yZB2SP6sU3MIYAOXwLMff0tVcCqO_/view?usp=sharing)

---

## 🚀 Features

* Visualize Medicare payments by diagnosis, age group, state, and chronic conditions
* Filter data interactively (state, age group, condition)
* Predict individual cost using diagnosis/procedure codes and chronic conditions
* Upload CSV for batch prediction

---

## 📦 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/ShreeyaBadhe/medoptix.git
cd medoptix
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up MySQL Database

Ensure you have a MySQL server running (locally or on AWS RDS) and import your cleaned `claims` and `beneficiary_info` tables.

Update the credentials in `config/db_config.py`:

```python
DB_CONFIG = {
    'host': 'your-hostname',
    'user': 'your-username',
    'password': 'your-password',
    'database': 'your-database'
}
```

> ⚠️ For security, avoid committing real credentials. Use [Streamlit secrets](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management) or environment variables in production.

### 4. Download Pretrained Models (Auto Download)

The app automatically downloads `.joblib` model files from Google Drive on the first run.

### 5. Run the Streamlit App

```bash
streamlit run app.py
```

---

## 📁 Project Structure

```bash
├── app.py                       # Main Streamlit dashboard
├── config/
│   └── db_config.py             # MySQL credentials
├── models/                      # Model files (.joblib - auto-downloaded)
├── analysis/                    # Supporting analysis scripts
├── sql/                         # Database schema and queries
├── requirements.txt             # Python dependencies
└── README.md
```

---

## 🛠 Requirements

* Python 3.8+
* Streamlit
* Pandas
* MySQL Connector
* Plotly
* Joblib
* gdown

Install all via:

```bash
pip install -r requirements.txt
```

---

## 🤝 Contributing

Feel free to fork this repository, add new visualizations, or plug in new models. Open a PR if you think your changes can help others!

---

## 📜 License

This project is open-source under the MIT License.
