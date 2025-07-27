import streamlit as st
import os

if "DB_CONFIG" in st.secrets:
    DB_CONFIG = dict(st.secrets["DB_CONFIG"])
else:
    # fallback to environment variables for local dev
    DB_CONFIG = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME'),
        'port': int(os.getenv('DB_PORT', 3306))
    }
