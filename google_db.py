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

# 🎯 새로 추가된 '단어 등록' 담당 업무
def add_word_to_sheet(sheet_name, word, meaning, note=""):
    client = get_google_client()
    sh = client.open(sheet_name)
    worksheet = sh.sheet1
    worksheet.append_row([word, meaning, note])

# 🎯 새로 추가된 '단어 수정' 담당 업무
def edit_word_in_sheet(sheet_name, old_word, new_word, new_mean, new_note=""):
    client = get_google_client()
    worksheet = client.open(sheet_name).sheet1
    try:
        # 기존 단어가 몇 번째 줄에 있는지 찾기
        cell = worksheet.find(old_word, in_column=1)
        if cell:
            # 찾은 줄의 A~C열 데이터를 새 내용으로 덮어쓰기
            worksheet.update(f'A{cell.row}:C{cell.row}', [[new_word, new_mean, new_note]])
    except Exception as e:
        pass

# 🎯 새로 추가된 '단어 삭제' 담당 업무
def delete_word_from_sheet(sheet_name, word):
    client = get_google_client()
    worksheet = client.open(sheet_name).sheet1
    try:
        cell = worksheet.find(word, in_column=1)
        if cell:
            # 찾은 줄을 통째로 삭제
            worksheet.delete_rows(cell.row)
    except Exception as e:
        pass

# 🎯 새로 추가된 '학습 통계 관리' 업무
def init_stats_sheet(sheet_name):
    client = get_google_client()
    sh = client.open(sheet_name)
    try:
        worksheet = sh.worksheet("통계")
    except:
        # 통계 탭이 없으면 자동으로 새로 만듭니다!
        worksheet = sh.add_worksheet(title="통계", rows="1000", cols="3")
        worksheet.append_row(["단어", "맞춘횟수", "틀린횟수"])
    return worksheet

def load_stats(sheet_name):
    worksheet = init_stats_sheet(sheet_name)
    records = worksheet.get_all_values()[1:] # 첫 줄(제목) 제외하고 읽기
    stats = {}
    for row in records:
        if len(row) >= 3:
            stats[row[0]] = {"correct": int(row[1]), "wrong": int(row[2])}
    return stats

def save_stats(sheet_name, stats_dict):
    if not sheet_name: # 시트 이름이 없으면 중단
        return False
    try:
        worksheet = init_stats_sheet(sheet_name)
        worksheet.clear() 
        rows = [["단어", "맞춘횟수", "틀린횟수"]]
        for w, data in stats_dict.items():
            rows.append([w, data.get("correct", 0), data.get("wrong", 0)])
        worksheet.update("A1", rows)
        return True
    except Exception as e:
        print(f"저장 중 오류 발생: {e}")
        return False

# 🎯 여러 시트의 데이터를 하나로 합쳐서 가져오는 업무
def load_multiple_sheets(sheet_names):
    all_words = {}
    all_notes = {}
    all_stats = {}
    
    for name in sheet_names:
        try:
            # 단어 로드
            w, n = load_words_from_sheet(name)
            all_words.update(w)
            all_notes.update(n)
            
            # 통계 로드
            s = load_stats(name)
            all_stats.update(s)
        except:
            continue # 에러 나는 시트는 건너뜁니다.
            
    return all_words, all_notes, all_stats
