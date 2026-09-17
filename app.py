import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

st.title("Shisa Kanko Examination Portal")
st.subheader("Phase 2 測試：Google Sheets 連線與 Voucher 驗證")

# 1. 從 Streamlit Secrets 讀取 Google 憑證
try:
  creds_dict = dict(st.secrets["gcp_service_account"])
  scopes = [
      "https://www.googleapis.com/auth/spreadsheets",
      "https://www.googleapis.com/auth/drive",
  ]
  creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
  client = gspread.authorize(creds)

  # 2. 開啟你的 Google 試算表（請確認試算表名稱完全一致）
  sheet_name = "ShisaKanko_Exam_Database"
  sh = client.open(sheet_name)

  # 3. 讀取 Vouchers 分頁的所有資料
  worksheet = sh.worksheet("Vouchers")
  data = worksheet.get_all_records()

  st.success("成功連線至 Google Sheets 試算表！")
  st.write("目前資料庫中的 Voucher 列表：")
  st.dataframe(data)

except Exception as e:
  st.error(f"連線失敗，請檢查 Secrets 或試算表名稱是否正確：{e}")
