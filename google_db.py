import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import json

# 서버가 시트를 반복해서 부르지 않도록 기억(캐싱)해주는 기능
@st.cache_resource
def get_google_client():
    # 비밀 금고에서 인증서 꺼내기
    creds_dict = json.loads(st.secrets["google_credentials"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def load_words_from_sheet(sheet_name):
    client = get_google_client()
    sh = client.open(sheet_name)
    worksheet = sh.sheet1
    records = worksheet.get_all_values()
    
    words = {}
    notes = {}
    # 첫 번째 줄(제목)부터 끝까지 읽으며 데이터 정리
    for row in records:
        if not row or len(row) < 2 or row[0].strip() in ["단어", ""]:
            continue
        w = row[0].strip()
        words[w] = row[1].strip()
        if len(row) >= 3:
            notes[w] = row[2].strip()
            
    return words, notes
