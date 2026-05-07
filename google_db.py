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
    if not sheet_name:
        return False
    try:
        worksheet = init_stats_sheet(sheet_name)
        worksheet.clear() 
        # 열(Column) 5개로 확장
        rows = [["단어", "맞춘횟수", "틀린횟수", "레벨", "다음복습일"]]
        for w, data in stats_dict.items():
            rows.append([
                w, 
                data.get("correct", 0), 
                data.get("wrong", 0),
                data.get("level", 0),
                data.get("next_review", "")
            ])
        worksheet.update("A1", rows)
        return True
    except Exception as e:
        print(f"저장 오류: {e}")
        return False
        
# 🎯 여러 시트의 데이터를 하나로 합쳐서 가져오는 업무
def load_multiple_sheets(sheet_names):
    combined_words = {}
    combined_notes = {}
    combined_stats = {}
    for sheet_name in sheet_names:
        # 1. 단어 로드
        try:
            w_sheet = client.open(sheet_name).worksheet("단어장")
            records = w_sheet.get_all_values()
            for row in records[1:]:
                if len(row) >= 2 and row[0]:
                    combined_words[row[0]] = row[1]
                    if len(row) >= 3:
                        combined_notes[row[0]] = row[2]
        except: pass

        # 2. 통계 로드 (레벨과 다음복습일 추가)
        try:
            s_sheet = client.open(sheet_name).worksheet("통계")
            s_records = s_sheet.get_all_values()
            for row in s_records[1:]:
                if len(row) >= 1 and row[0]:
                    w = row[0]
                    c = int(row[1]) if len(row) > 1 and row[1].isdigit() else 0
                    w_cnt = int(row[2]) if len(row) > 2 and row[2].isdigit() else 0
                    lv = int(row[3]) if len(row) > 3 and row[3].isdigit() else 0
                    nr = row[4] if len(row) > 4 else ""
                    combined_stats[w] = {"correct": c, "wrong": w_cnt, "level": lv, "next_review": nr}
        except: pass

    return combined_words, combined_notes, combined_stats
