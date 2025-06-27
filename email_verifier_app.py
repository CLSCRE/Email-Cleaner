
import streamlit as st
import pandas as pd
import requests

# --- Authentication ---
CREDENTIALS = {"admin": "mypassword", "user": "test123"}
auth_placeholder = st.empty()
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with auth_placeholder.container():
        st.subheader("🔐 Login Required")
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if user in CREDENTIALS and CREDENTIALS[user] == pw:
                st.session_state.authenticated = True
                auth_placeholder.empty()
            else:
                st.error("Invalid credentials.")
    st.stop()

# --- App Title and Logo ---
st.image("https://clscre.com/wp-content/uploads/2023/01/CLS-CRE-LOGO-2023-white-background.png", width=200)  # Replace with your actual logo URL
st.title("📧 Email Cleaner +")

# File uploader and API key input
uploaded_file = st.file_uploader("Upload CoStar Spreadsheet", type=[".xlsx"])
api_key = st.secrets["ABSTRACT_API_KEY"]
st.success("🔑 Using stored Abstract API key from secrets.")

if uploaded_file and api_key:
    df = pd.read_excel(uploaded_file)
    email_cols = [col for col in df.columns if 'email' in col.lower()]

    if not email_cols:
        st.warning("No email columns found with 'email' in the header.")
    else:
        emails = pd.unique(df[email_cols].values.ravel())
        valid_emails = [e for e in emails if isinstance(e, str) and "@" in e]

        st.write(f"✅ Found {len(valid_emails)} valid emails. Starting verification...")

        def verify_email(email):
            url = "https://emailvalidation.abstractapi.com/v1/"
            params = {"api_key": api_key, "email": email}
            try:
                response = requests.get(url, params=params)
                if response.ok:
                    data = response.json()
                    return {
                        "email": email,
                        "is_valid_format": data["is_valid_format"]["value"],
                        "is_mx_found": data["is_mx_found"]["value"],
                        "is_smtp_valid": data["is_smtp_valid"]["value"],
                        "is_disposable": data["is_disposable_email"]["value"],
                        "is_role": data["is_role_email"]["value"],
                        "quality_score": data["quality_score"]
                    }
                else:
                    return {"email": email, "error": response.status_code}
            except Exception as e:
                return {"email": email, "error": str(e)}

        results = [verify_email(email) for email in valid_emails]

        result_df = pd.DataFrame(results)
        st.success("Verification complete!")
        st.dataframe(result_df)

        csv = result_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Results as CSV", csv, "verified_emails.csv", "text/csv")
