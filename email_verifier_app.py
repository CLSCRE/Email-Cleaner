
import streamlit as st
import pandas as pd
import requests
import time
from io import BytesIO

# --- Authentication ---
CREDENTIALS = {"trevor@clscre.com": "Clscre654321@"}
auth_placeholder = st.empty()
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with auth_placeholder.container():
        st.markdown("""<h2 style='text-align:center;'>🔐 Login Required</h2>""", unsafe_allow_html=True)
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if user in CREDENTIALS and CREDENTIALS[user] == pw:
                st.session_state.authenticated = True
                auth_placeholder.empty()
                st.rerun()
            else:
                st.error("Invalid credentials.")
    st.stop()

# --- Animated Logo & Welcome ---
st.markdown("""
    <style>
        @keyframes float {
            0% { transform: translatey(0px); }
            50% { transform: translatey(-10px); }
            100% { transform: translatey(0px); }
        }
        .floating-logo {
            animation: float 3s ease-in-out infinite;
        }
    </style>
    <div style="text-align:center;">
        <img src="https://clscre.com/wp-content/uploads/2023/01/CLS-CRE-LOGO-2023-white-background.png" width="200" class="floating-logo"/>
    </div>
""", unsafe_allow_html=True)

st.markdown("""<h1 style='text-align:center;'>📧 Email Cleaner +</h1>""", unsafe_allow_html=True)
st.markdown("""<p style='text-align:center;'>Upload your spreadsheet to validate emails using Abstract API</p>""", unsafe_allow_html=True)

# --- File upload & API key ---
uploaded_file = st.file_uploader("📤 Upload CoStar Spreadsheet (.xlsx)", type=[".xlsx"])
api_key = st.secrets["ABSTRACT_API_KEY"]

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    email_cols = [col for col in df.columns if 'email' in col.lower()]

    if not email_cols:
        st.warning("⚠️ No email columns found with 'email' in the header.")
    else:
        emails = pd.unique(df[email_cols].values.ravel())
        total_scanned = len(emails)
        valid_emails = [e for e in emails if isinstance(e, str) and "@" in e]
        blanks = total_scanned - len(valid_emails)

        st.info(f"📄 Scanned {total_scanned} cells — Found {len(valid_emails)} valid emails, {blanks} blank/skipped.")

        if len(valid_emails) == 0:
            st.warning("⚠️ No valid email addresses found in your file.")
        else:
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

            st.info("⏳ Verifying emails... please wait")
            progress = st.progress(0)
            results = []
            for i, email in enumerate(valid_emails):
                results.append(verify_email(email))
                progress.progress((i + 1) / len(valid_emails))
                time.sleep(0.35)

            result_df = pd.DataFrame(results)
            st.success("✅ Verification complete!")
            st.dataframe(result_df)

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
