from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

st.title("Shisa Kanko Examination Portal")
st.subheader("Candidate Identity Verification & Registration")


# Connect to Google Sheets
@st.cache_resource
def get_google_sheet():
  creds_dict = dict(st.secrets["gcp_service_account"])
  scopes = [
      "https://www.googleapis.com/auth/spreadsheets",
      "https://www.googleapis.com/auth/drive",
  ]
  creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
  client = gspread.authorize(creds)
  return client.open("ShisaKanko_Exam_Database")


# Initialize session state variables
if "verified" not in st.session_state:
  st.session_state.verified = False
if "user_email" not in st.session_state:
  st.session_state.user_email = ""
if "english_name" not in st.session_state:
  st.session_state.english_name = ""
if "japanese_name" not in st.session_state:
  st.session_state.japanese_name = ""
if "voucher_code" not in st.session_state:
  st.session_state.voucher_code = ""

try:
  sh = get_google_sheet()
  worksheet = sh.worksheet("Vouchers")

  if not st.session_state.verified:
    st.markdown("### Step 1: Real-time Voucher Verification")
    voucher_input = st.text_input(
        "Enter your Examination Voucher Code"
    ).strip()

    if voucher_input:
      records = worksheet.get_all_records()
      matched_record = None
      r_index = None

      for idx, record in enumerate(records):
        if str(record.get("VoucherCode")).strip() == voucher_input:
          r_index = idx + 2
          matched_record = record
          break

      if not matched_record:
        st.error(
            "❌ Invalid Voucher Code. Please check and re-enter your code."
        )
      elif matched_record.get("Status") != "Active":
        st.error(
            "⚠️ This Voucher has already been used or is inactive and cannot be"
            " reused!"
        )
      else:
        st.success(
            "✅ Valid Voucher! Please complete your candidate details below to"
            " proceed."
        )

        st.markdown("---")
        st.markdown("### Step 2: Candidate Information")

        email_1 = st.text_input("Email Address")
        email_2 = st.text_input("Confirm Email Address")

        col1, col2 = st.columns([3, 1])
        with col1:
          english_name = st.text_input(
              "Full Name (as per ID/Passport)"
          )
        with col2:
          st.write("")
          st.write("")
          translate_btn = st.button("🇯🇵 Katakana Helper")

        if "jp_name_temp" not in st.session_state:
          st.session_state.jp_name_temp = ""

        if translate_btn and english_name:
          st.session_state.jp_name_temp = (
              f"[{english_name} - Katakana equivalent placeholder]"
          )

        japanese_name_input = st.text_input(
            "Japanese Name / Katakana (Editable for certificate display)",
            value=st.session_state.jp_name_temp,
        )

        st.markdown("---")

        confirm_checkbox = st.checkbox(
            "I confirm that the email and name provided above are correct."
            " Note: Data cannot be changed after submission!"
        )

        if st.button("🚀 Confirm and Lock Voucher to Enter Exam"):
          if not email_1 or not email_2 or not english_name:
            st.warning("Please fill in all required fields.")
          elif email_1 != email_2:
            st.error("❌ Email addresses do not match. Please check again!")
          elif not confirm_checkbox:
            st.warning(
                "⚠️ Please check the confirmation box acknowledging that data"
                " cannot be changed after submission."
            )
          else:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Update Google Sheet cells
            worksheet.update_cell(r_index, 2, "Used")  # Status -> Col B
            worksheet.update_cell(r_index, 3, email_1)  # AssignedEmail -> Col C
            worksheet.update_cell(r_index, 4, now_str)  # UsedTime -> Col D
            worksheet.update_cell(
                r_index, 6, english_name
            )  # EnglishName -> Col F
            worksheet.update_cell(
                r_index, 7, japanese_name_input
            )  # JapaneseName -> Col G

            st.session_state.verified = True
            st.session_state.user_email = email_1
            st.session_state.english_name = english_name
            st.session_state.japanese_name = japanese_name_input
            st.session_state.voucher_code = voucher_input

            st.success(
                "🎉 Verification & Registration Successful! Voucher has been"
                " locked."
            )
            st.rerun()

  else:
    st.success(
        f"Welcome Candidate: **{st.session_state.english_name}**"
        f" ({st.session_state.user_email})"
    )
    st.info(
        "📌 Your Voucher is successfully locked. Ready to proceed to the"
        " examination modules."
    )

    if st.button("Start Examination (Proceed to Next Stage)"):
      st.balloons()

except Exception as e:
  st.error(f"System connection or processing error: {e}")
