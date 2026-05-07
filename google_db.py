import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# 구글 시트 연결 설정
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_gspread_client():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

client = get_gspread_client()

# ==========================================
# 🎯 [신규] 영구 설정(시트 목록 및 순서) 저장소
# ==========================================
def get_config_sheet():
    config_name = "VEHA_FLASHCARD_CONFIG"
    try:
        sh = client.open(config_name)
    except gspread.exceptions.SpreadsheetNotFound:
        # 봇이 스스로 숨겨진 마스터 설정 파일을 만듭니다.
        sh = client.create(config_name)
    return sh.sheet1

def load_user_sheets(username):
    try:
        ws = get_config_sheet()
        records = ws.get_all_values()
        for row in records:
            if row and row[0] == username:
                return row[1:] # 0번째(이름)을 제외한 나머지 시트 목록 반환
    except: pass
    return []

def save_user_sheets(username, sheet_list):
    try:
        ws = get_config_sheet()
        records = ws.get_all_values()
        row_idx = -1
        for i, row in enumerate(records):
            if row and row[0] == username:
                row_idx = i + 1
                break
        
        if row_idx != -1:
            ws.delete_rows(row_idx) # 기존 기록 삭제
            
        ws.append_row([username] + sheet_list) # 새 순서대로 덮어쓰기
        return True
    except: return False

# ==========================================
# 기존 단어장 & 통계 로직
# ==========================================
def init_stats_sheet(sheet_name, username):
    sh = client.open(sheet_name)
    tab_title = f"통계_{username}"
    try:
        worksheet = sh.worksheet(tab_title)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title=tab_title, rows="1000", cols="5")
        worksheet.append_row(["단어", "맞춘횟수", "틀린횟수", "레벨", "다음복습일"])
    return worksheet

def load_multiple_sheets(sheet_names, username):
    combined_words = {}
    combined_notes = {}
    combined_stats = {}
    error_msg = ""
    
    for sheet_name in sheet_names:
        try:
            sh = client.open(sheet_name.strip())
            try:
                w_sheet = sh.worksheet("단어장")
                records = w_sheet.get_all_values()
                for row in records[1:]:
                    if len(row) >= 2 and row[0]:
                        combined_words[row[0]] = row[1]
                        if len(row) >= 3: combined_notes[row[0]] = row[2]
            except gspread.exceptions.WorksheetNotFound:
                error_msg = f"'{sheet_name}' 파일 안에 '단어장' 탭이 없습니다."
                continue

            try:
                tab_title = f"통계_{username}"
                s_sheet = sh.worksheet(tab_title)
                s_records = s_sheet.get_all_values()
                for row in s_records[1:]:
                    if len(row) >= 1 and row[0]:
                        w = row[0]
                        c = int(row[1]) if len(row) > 1 and row[1].isdigit() else 0
                        w_cnt = int(row[2]) if len(row) > 2 and row[2].isdigit() else 0
                        lv = int(row[3]) if len(row) > 3 and row[3].isdigit() else 0
                        nr = row[4] if len(row) > 4 else ""
                        combined_stats[w] = {"correct": c, "wrong": w_cnt, "level": lv, "next_review": nr}
            except gspread.exceptions.WorksheetNotFound: pass
                
        except gspread.exceptions.SpreadsheetNotFound:
            error_msg = f"'{sheet_name}' 파일을 찾을 수 없거나 공유되지 않았습니다."
        except Exception as e:
            error_msg = f"알 수 없는 오류 발생: {str(e)}"

    return combined_words, combined_notes, combined_stats, error_msg

def save_stats(sheet_name, stats_dict, username):
    if not sheet_name or not username: return False
    try:
        worksheet = init_stats_sheet(sheet_name, username)
        worksheet.clear() 
        rows = [["단어", "맞춘횟수", "틀린횟수", "레벨", "다음복습일"]]
        for w, data in stats_dict.items():
            rows.append([w, data.get("correct", 0), data.get("wrong", 0), data.get("level", 0), data.get("next_review", "")])
        worksheet.update("A1", rows)
        return True
    except: return False

def add_word_to_sheet(sheet_name, word, mean, note):
    try:
        sh = client.open(sheet_name)
        w_sheet = sh.worksheet("단어장")
        w_sheet.append_row([word, mean, note])
        return True
    except: return False

def edit_word_in_sheet(sheet_name, old_word, new_word, new_mean, new_note):
    try:
        sh = client.open(sheet_name)
        w_sheet = sh.worksheet("단어장")
        cell = w_sheet.find(old_word)
        w_sheet.update_row(cell.row, [new_word, new_mean, new_note])
        return True
    except: return False

def delete_word_from_sheet(sheet_name, word):
    try:
        sh = client.open(sheet_name)
        w_sheet = sh.worksheet("단어장")
        cell = w_sheet.find(word)
        w_sheet.delete_rows(cell.row)
        return True
    except: return False
