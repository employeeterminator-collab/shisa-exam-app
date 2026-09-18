from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# Hide Streamlit menu, header, footer, toolbar, and floating branding badge
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {display: none !important; visibility: hidden !important;}
    [data-testid="stDecoration"] {display: none !important; visibility: hidden !important;}
    [data-testid="stStatusWidget"] {display: none !important; visibility: hidden !important;}
    .viewerBadge_container__1QSob {display: none !important; visibility: hidden !important;}
    div[class*="viewerBadge"] {display: none !important; visibility: hidden !important;}
    .stDeployButton {display: none !important; visibility: hidden !important;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("Shisa Kanko-Shi&TM")
st.subheader("(Certified Pointing-and-Calling Specialist)") 
st.title("Examination Registration Portal")
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

        st.markdown("#### English Name (as per ID/Passport)")
        col_en1, col_en2 = st.columns(2)
        with col_en1:
          english_first_name = st.text_input("English First Name")
        with col_en2:
          english_last_name = st.text_input("English Last Name")

        # Japanese Name Section with Help Button
        col_jp_label, col_jp_btn = st.columns([2, 1])
        with col_jp_label:
          st.markdown("#### Japanese Name")
        with col_jp_btn:
          st.write("")  # Alignment spacer
          st.link_button(
              "Help with Japanese Name",
              "https://exam1.shisakanko.org/Converter.html",
              use_container_width=True,
          )

        japanese_name = st.text_input(
            "Japanese Name (Katakana / Kanji — Family Name first)"
        )

        st.markdown("---")

        confirm_checkbox = st.checkbox(
            "I confirm that the email and names provided above are correct."
            " Note: Data cannot be changed after submission!"
        )

        if st.button("🚀 Confirm and Lock Voucher"):
          if (
              not email_1
              or not email_2
              or not english_first_name
              or not english_last_name
          ):
            st.warning("Please fill in all required email and English name fields.")
          elif email_1 != email_2:
            st.error(
                "❌ Error: Both email addresses do not match. Please check"
                " again!"
            )
          elif not confirm_checkbox:
            st.warning(
                "⚠️ Please check the confirmation box acknowledging that data"
                " cannot be changed after submission."
            )
          else:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Update Google Sheet cells (Mapping:
            # Col F: EnglishFirstName, Col G: EnglishLastName, Col H: JapaneseName)
            worksheet.update_cell(r_index, 2, "Used")  # Status -> Col B
            worksheet.update_cell(r_index, 3, email_1)  # AssignedEmail -> Col C
            worksheet.update_cell(r_index, 4, now_str)  # UsedTime -> Col D
            worksheet.update_cell(r_index, 6, english_first_name)  # Col F
            worksheet.update_cell(r_index, 7, english_last_name)  # Col G
            worksheet.update_cell(r_index, 8, japanese_name)  # Col H

            st.session_state.verified = True
            st.session_state.user_email = email_1
            st.session_state.voucher_code = voucher_input

            st.success(
                "🎉 Registration Successful! Voucher has been locked."
            )
            st.rerun()

  else:
    # Post-verification screen layout
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        "<h3 style='text-align: center;'>Exam Voucher has been validated and"
        " registered. You will need your email address and voucher to launch"
        " your exam.</h3>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    with col_c2:
      st.link_button(
          "Return to Shisa Kanko Promotion Institute",
          "https://shisakanko.org",
          use_container_width=True,
      )

except Exception as e:
  st.error(f"System connection or processing error: {e}")
