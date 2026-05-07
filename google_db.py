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
# 🎯 시트 목록 영구 저장소
# ==========================================
def get_config_sheet():
    config_name = "시트 영구 저장소"
    try:
        sh = client.open(config_name)
        return sh.sheet1
    except gspread.exceptions.SpreadsheetNotFound:
        raise Exception(f"'{config_name}' 파일을 찾을 수 없습니다. 봇 이메일 편집자 공유를 확인해주세요.")

def load_user_sheets(username):
    try:
        ws = get_config_sheet()
        records = ws.get_all_values()
        for row in records:
            if row and row[0] == username:
                return row[1:] 
    except Exception as e: 
        return str(e) 
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
            ws.delete_rows(row_idx) 
        ws.append_row([username] + sheet_list) 
        return True
    except Exception as e: 
        return str(e)

# ==========================================
# 🎯 학습 범위 & 카드 방향 설정 저장소
# ==========================================
def get_settings_sheet():
    config_name = "시트 영구 저장소"
    try:
        sh = client.open(config_name)
        try:
            worksheet = sh.worksheet("설정")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title="설정", rows="1000", cols="3")
            worksheet.append_row(["사용자", "학습범위", "카드방향"])
        return worksheet
    except gspread.exceptions.SpreadsheetNotFound:
        raise Exception(f"'{config_name}' 파일을 찾을 수 없습니다.")

def load_user_settings(username):
    try:
        ws = get_settings_sheet()
        records = ws.get_all_values()
        for row in records[1:]:
            if row and row[0] == username:
                if len(row) >= 3:
                    return row[1], row[2]
    except Exception:
        pass
    return "전체 단어 (오답 우선)", "단어 ➔ 뜻"

def save_user_settings(username, study_target, card_direction):
    try:
        ws = get_settings_sheet()
        records = ws.get_all_values()
        row_idx = -1
        for i, row in enumerate(records):
            if row and row[0] == username:
                row_idx = i + 1
                break
        if row_idx != -1:
            ws.delete_rows(row_idx) 
        ws.append_row([username, study_target, card_direction])
        return True
    except Exception as e:
        return str(e)

# ==========================================
# 🎯 [신규] '다중 페이지' 노트북 저장소!
# ==========================================
def get_notebook_sheet():
    config_name = "시트 영구 저장소"
    try:
        sh = client.open(config_name)
        try:
            # 안전하게 새로운 이름의 탭을 만듭니다. (3칸짜리)
            worksheet = sh.worksheet("노트북_다중")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title="노트북_다중", rows="1000", cols="3")
            worksheet.append_row(["사용자", "페이지제목", "내용"])
        return worksheet
    except gspread.exceptions.SpreadsheetNotFound:
        raise Exception(f"'{config_name}' 파일을 찾을 수 없습니다.")

def load_user_notebooks(username):
    try:
        ws = get_notebook_sheet()
        records = ws.get_all_values()
        notebooks = {}
        for row in records[1:]:
            if row and len(row) >= 3 and row[0] == username:
                notebooks[row[1]] = row[2] # 딕셔너리 형태로 여러 페이지를 담아옴
        return notebooks
    except Exception:
        return {}

def save_user_notebook_page(username, page_title, content):
    try:
        ws = get_notebook_sheet()
        records = ws.get_all_values()
        row_idx = -1
        for i, row in enumerate(records):
            if row and len(row) >= 2 and row[0] == username and row[1] == page_title:
                row_idx = i + 1
                break
        if row_idx != -1:
            ws.update_cell(row_idx, 3, content) # 기존 페이지는 내용만 덮어쓰기
        else:
            ws.append_row([username, page_title, content]) # 새 페이지는 새로 추가
        return True
    except Exception as e:
        return str(e)

def delete_user_notebook_page(username, page_title):
    try:
        ws = get_notebook_sheet()
        records = ws.get_all_values()
        row_idx = -1
        for i, row in enumerate(records):
            if row and len(row) >= 2 and row[0] == username and row[1] == page_title:
                row_idx = i + 1
                break
        if row_idx != -1:
            ws.delete_rows(row_idx) # 해당 페이지(행) 아예 삭제
        return True
    except Exception as e:
        return str(e)

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
            error_msg = f"오류: {str(e)}"
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
