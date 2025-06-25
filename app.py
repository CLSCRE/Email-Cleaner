import streamlit as st
import pandas as pd
import requests
import time

API_KEY = st.secrets["EMAILABLE_API_KEY"]
BASE_URL = "https://api.emailable.com/v1/verify"

def extract_emails(df):
    email_cols = [col for col in df.columns if 'email' in col.lower()]
    raw_emails = df[email_cols].values.flatten()
    emails = pd.Series(raw_emails).dropna().astype(str).str.strip().str.lower()
    return emails.drop_duplicates()

def enrich_email(email):
    try:
        response = requests.get(BASE_URL, params={
            'api_key': API_KEY,
            'email': email
        })
        data = response.json()
        return {
            'Email': email,
            'Valid Format': data.get('format'),
            'Deliverable': data.get('deliverable'),
            'MX Found': data.get('mx'),
            'SMTP Check': data.get('smtp'),
            'Is Free Email': data.get('free'),
            'Is Disposable': data.get('disposable'),
            'Domain': data.get('domain'),
            'Quality Score': data.get('score')
        }
    except Exception as e:
        return {'Email': email, 'Error': str(e)}

st.set_page_config(page_title="CLS CRE Email Enrichment Tool", layout="wide")
st.image("https://clscre.com/wp-content/uploads/2023/05/CLS-CRE_logo_white.png", width=200)
st.markdown("<h4>📧 Email Address Enrichment Tool</h4>", unsafe_allow_html=True)

st.caption("Upload a spreadsheet with email addresses to validate format, deliverability, and domain type.")

uploaded_file = st.file_uploader("Upload Excel or CSV File", type=["xlsx", "xls", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    emails = extract_emails(df)
    st.success(f"Found {len(emails)} unique email addresses.")

    enriched = []
    progress = st.progress(0)
    for i, email in enumerate(emails):
        enriched.append(enrich_email(email))
        progress.progress((i + 1) / len(emails))
        time.sleep(1)

    result_df = pd.DataFrame(enriched)
    st.dataframe(result_df)

    csv = result_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Enriched Emails as CSV",
        data=csv,
        file_name="enriched_emails.csv",
        mime='text/csv'
    )
