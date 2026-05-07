import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# 구글 시트 연결 설정
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_gspread_client():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

client = get_gspread_client()

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
    error_msg = "" # 에러 추적용
    
    for sheet_name in sheet_names:
        try:
            # 1. 파일 열기 시도
            sh = client.open(sheet_name.strip())
            
            # 2. 단어장 탭 로드
            try:
                w_sheet = sh.worksheet("단어장")
                records = w_sheet.get_all_values()
                for row in records[1:]:
                    if len(row) >= 2 and row[0]:
                        combined_words[row[0]] = row[1]
                        if len(row) >= 3:
                            combined_notes[row[0]] = row[2]
            except gspread.exceptions.WorksheetNotFound:
                error_msg = f"'{sheet_name}' 파일 안에 '단어장'이라는 이름의 탭이 없습니다."
                continue

            # 3. 사용자 통계 탭 로드
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
            except gspread.exceptions.WorksheetNotFound:
                # 통계 탭이 없는건 오류가 아니므로(처음 접속 시) 자동 생성 로직이 처리함
                pass
                
        except gspread.exceptions.SpreadsheetNotFound:
            error_msg = f"구글 드라이브에서 '{sheet_name}' 파일을 찾을 수 없습니다. 이름이 정확한지, 봇 이메일이 공유되었는지 확인해주세요."
        except Exception as e:
            error_msg = f"알 수 없는 오류 발생: {str(e)}"

    return combined_words, combined_notes, combined_stats, error_msg

def save_stats(sheet_name, stats_dict, username):
    if not sheet_name or not username:
        return False
    try:
        worksheet = init_stats_sheet(sheet_name, username)
        worksheet.clear() 
        rows = [["단어", "맞춘횟수", "틀린횟수", "레벨", "다음복습일"]]
        for w, data in stats_dict.items():
            rows.append([w, data.get("correct", 0), data.get("wrong", 0), data.get("level", 0), data.get("next_review", "")])
        worksheet.update("A1", rows)
        return True
    except:
        return False

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
