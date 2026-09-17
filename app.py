from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

st.title("Shisa Kanko Examination Portal")
st.subheader("Voucher Validation and Registration Test")

# 建立 Google Sheets 連線函式
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


try:
  sh = get_google_sheet()
  worksheet = sh.worksheet("Vouchers")

  # 建立一個簡單的輸入表單
  with st.form("voucher_form"):
    user_email = st.text_input("Please fill in your email address")
    voucher_input = st.text_input("Please fill in Voucher Code)")
    submit_button = st.form_submit_button("Validate Voucher")

  if submit_button:
    if not user_email or not voucher_input:
      st.warning("Please fill in your Email and Voucher Code。")
    else:
      # 取得所有紀錄以尋找對應的 Voucher
      records = worksheet.get_all_records()
      row_index = None
      matched_row = None

      # 尋找對應的 Voucher (從第 2 列開始算，因為 row 1 是標題，所以 index 要 +2)
      for idx, record in enumerate(records):
        if str(record.get("VoucherCode")).strip() == voucher_input.strip():
          row_index = idx + 2
          matched_row = record
          break

      if not matched_row:
        st.error("Voucher not found. Please confirm and re-enter。")
      elif matched_row.get("Status") != "Active":
        st.error(
            "This voucher has been used or expired and cannot be reused!"
        )
      else:
        # 驗證成功！更新 Google Sheet 狀態為 Used，並寫入 Email 與時間
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 更新 Status (Col B), AssignedEmail (Col C), UsedTime (Col D)
        worksheet.update_cell(row_index, 2, "Used")
        worksheet.update_cell(row_index, 3, user_email)
        worksheet.update_cell(row_index, 4, now_str)

        st.success(
            f"Voucher verification successful! Successfully bound to {user_email}, proceeding to the next exam interface."
        )
        # 這裡未來可以透過 st.session_state 進入下一步

except Exception as e:
  st.error(f"系統連線或讀取發生錯誤：{e}")
