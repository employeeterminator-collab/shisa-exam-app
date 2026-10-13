import json
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# ==========================================
# Idle session killer — cost guard (5 min)
# ==========================================
# Ends the browser session after 5 minutes with no mouse /
# keyboard / touch input. 60s before the kill, a full-screen warning with
# countdown appears; any input cancels it. The kill navigates the top page
# away, which drops the Streamlit websocket and frees the Cloud Run instance.
st.components.v1.html(
    """
    <script>
    (function() {
        var TIMEOUT_MS = 5 * 60 * 1000;
        var WARN_AT_MS = TIMEOUT_MS - 60 * 1000;
        var KEY = '__idleLastActivityAtshisaexam';
        function now() { return Date.now(); }
        try {
            if (!parent.window[KEY]) parent.window[KEY] = now();
            if (parent.window.__idleWatchershisaexam) return;
            parent.window.__idleWatchershisaexam = true;
        } catch (e) { return; }
        function touch() { try { parent.window[KEY] = now(); } catch (e) {} }
        ['mousemove', 'mousedown', 'keydown', 'touchstart', 'click', 'scroll'].forEach(function(ev) {
            try { parent.document.addEventListener(ev, touch, {passive: true}); } catch (e) {}
        });
        var warned = false;
        var overlay = null;
        var countdownEl = null;
        function showWarning() {
            try {
                overlay = parent.document.createElement('div');
                overlay.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;'
                    + 'background:rgba(0,0,0,0.85);z-index:2147483647;display:flex;'
                    + 'align-items:center;justify-content:center;flex-direction:column;'
                    + 'color:#fff;font-family:sans-serif;text-align:center;padding:24px;box-sizing:border-box;';
                overlay.innerHTML = '<div style="font-size:22px;font-weight:bold;margin-bottom:12px;">Session expiring due to inactivity</div>'
                    + '<div style="font-size:15px;opacity:0.9;">No activity detected for 5 minutes.<br>'
                    + 'This session will end in <span id="__idleCountdown" style="font-weight:bold;">60</span> seconds.<br>'
                    + 'Move your mouse or press any key to continue.</div>';
                parent.document.body.appendChild(overlay);
                countdownEl = overlay.querySelector('#__idleCountdown');
            } catch (e) {}
        }
        function hideWarning() {
            try { if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay); } catch (e) {}
            overlay = null; warned = false;
        }
        function killSession() {
            try {
                if (overlay) overlay.innerHTML = '<div style="font-size:22px;font-weight:bold;">Session ended</div>'
                    + '<div style="font-size:15px;opacity:0.9;margin-top:12px;">Closed due to inactivity. You may close this tab.</div>';
            } catch (e) {}
            setTimeout(function() {
                try { parent.window.location.href = 'about:blank'; } catch (e) {}
            }, 3000);
        }
        setInterval(function() {
            var last;
            try { last = parent.window[KEY] || now(); } catch (e) { return; }
            var idle = now() - last;
            if (idle >= TIMEOUT_MS) { killSession(); return; }
            if (idle >= WARN_AT_MS && !warned) { warned = true; showWarning(); }
            if (idle < WARN_AT_MS && warned) { hideWarning(); }
            if (warned && countdownEl) {
                countdownEl.textContent = Math.max(0, Math.ceil((TIMEOUT_MS - idle) / 1000));
            }
        }, 1000);
    })();
    </script>
    """,
    height=0,
)

# 隱藏 Streamlit 預設選單、頁尾與標題的錨點連結符號
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {display: none !important; visibility: hidden !important;}
    [data-testid="stDecoration"] {display: none !important; visibility: hidden !important;}
    [data-testid="stStatusWidget"] {display: none !important; visibility: hidden !important;}
    
    /* 隱藏所有 Markdown 標題的錨點連結圖示 */
    .stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a, .stMarkdown h4 a {
        display: none !important;
    }
    h1 a, h2 a, h3 a, h4 a {
        display: none !important;
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("Shisa Kanko-Shi\u2122")
st.markdown("<style>h1 { text-align: center; }</style>", unsafe_allow_html=True)
st.subheader("(Certified Pointing-and-Calling Specialist)") 
st.markdown("<style>h3 { text-align: center; }</style>", unsafe_allow_html=True)
st.title("Examination Registration Portal")
st.subheader("Candidate Identity Verification & Registration")
st.markdown("---")

# Connect to Google Sheets
@st.cache_resource
def get_google_sheet():
  scope = [
      "https://www.googleapis.com/auth/spreadsheets",
      "https://www.googleapis.com/auth/drive",
  ]

  try:
    service_account_info = json.loads(os.getenv("GCP_SERVICE_ACCOUNT"))
    creds = Credentials.from_service_account_info(
        service_account_info, scopes=scope
    )
    client = gspread.authorize(creds)

    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
      st.error("Missing SPREADSHEET_ID environment variable.")
      st.stop()

    # Return the spreadsheet object so sh is not None
    return client.open_by_key(spreadsheet_id)
  except Exception as e:
    st.error(f"Connection error: {e}")
    st.stop()

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
    st.markdown(
    "<h3 style='text-align: left;'>Step 1: Real-time Voucher Verification</h3>",
    unsafe_allow_html=True,)
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
        st.markdown( "<h3 style='text-align: left;'>Step 2: Candidate Information</h3>", unsafe_allow_html=True,)
      

        email_1 = st.text_input("Email Address")
        email_2 = st.text_input("Confirm Email Address")

        st.markdown("#### English Name (as per ID/Passport)")
        col_en1, col_en2 = st.columns(2)
        with col_en1:
          english_first_name = st.text_input("English First Name", max_chars=18)
        with col_en2:
          english_last_name = st.text_input("English Last Name", max_chars=12)

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
            "Japanese Name (Katakana / Kanji — Family Name first)",
            max_chars=11
        )

        st.markdown("---")

        confirm_checkbox = st.checkbox(
            "I confirm that the email and names provided above are correct."
            " Note: Data cannot be changed after submission!"
        )
        st.markdown("<br><br>", unsafe_allow_html=True)
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
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.success(
                "🎉 Registration Successful! Voucher has been locked."
            )
            st.rerun()
        st.markdown("---")
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
