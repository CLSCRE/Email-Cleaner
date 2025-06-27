import time

import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# --- Authentication ---
CREDENTIALS = {"trevor@clscre.com": "Clscre654321@"}
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
st.image("https://clscre.com/wp-content/uploads/2023/01/CLS-CRE-LOGO-2023-white-background.png", width=200)
st.title("📧 Email Cleaner +")

# File uploader and API key
uploaded_file = st.file_uploader("Upload CoStar Spreadsheet", type=[".xlsx"])
api_key = st.secrets["ABSTRACT_API_KEY"]
st.success("🔑 Using stored Abstract API key from secrets.")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    email_cols = [col for col in df.columns if 'email' in col.lower()]

    if not email_cols:
        st.warning("No email columns found with 'email' in the header.")
    else:
        emails = pd.unique(df[email_cols].values.ravel())
        total_scanned = len(emails)
        valid_emails = [e for e in emails if isinstance(e, str) and "@" in e]
        blanks = total_scanned - len(valid_emails)

        st.info(f"📄 Scanned {total_scanned} cells — Found {len(valid_emails)} valid emails, {blanks} blank/skipped.")

        def verify_email(email):
            url = "https://emailvalidation.abstractapi.com/v1/"
            params = {"api_key": api_key, "email": email}
            try:
                response = requests.get(url, params=params)
                if response.status_code == 429:
                    return {"email": email, "error": "Rate limited"}
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
                    return {"email": email, "error": f"HTTP {response.status_code}"}
            except Exception as e:
                return {"email": email, "error": str(e)}

        results = []
        for email in valid_emails:
            results.append(verify_email(email))
            time.sleep(0.35)
        result_df = pd.DataFrame(results)

        st.success("✅ Verification complete!")
        st.dataframe(result_df)

        # Combine original + results in Excel with two sheets
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name="Original Data", index=False)
            result_df.to_excel(writer, sheet_name="Verification Results", index=False)
        st.download_button(
            "📥 Download Excel with Results",
            data=output.getvalue(),
            file_name="email_verification_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
