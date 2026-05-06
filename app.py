import streamlit as st
import google_db
from gtts import gTTS
import io
import random

# 1. 브라우저 설정
st.set_page_config(page_title="Veha's English", page_icon="📖", layout="centered")

# 2. 앱의 기억력 세팅
if 'word_list' not in st.session_state:
    st.session_state.words = {}
    st.session_state.notes = {}
    st.session_state.word_list = []
    st.session_state.current_idx = 0
    st.session_state.show_meaning = False
    st.session_state.direction = "W2M"
    st.session_state.is_admin = False
    st.session_state.current_sheet = ""
    st.session_state.stats = {}
    st.session_state.saved_sheets = ["영어"] 
    
    st.session_state.test_active = False
    st.session_state.test_type = "객관식"
    st.session_state.test_q_max = 0
    st.session_state.test_q_count = 0
    st.session_state.test_queue = []
    st.session_state.test_score = 0
    st.session_state.test_answered = False
    st.session_state.test_options = []
    st.session_state.test_msg = ""

def get_audio_player(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp

def prepare_question():
    st.session_state.test_answered = False
    st.session_state.test_msg = ""
    current_w = st.session_state.test_queue[st.session_state.test_q_count]
    if st.session_state.test_type == "객관식":
        correct_m = st.session_state.words[current_w]
        pool_m = [st.session_state.words[w] for w in st.session_state.word_list if w != current_w]
        options = random.sample(pool_m, min(3, len(pool_m))) + [correct_m]
        random.shuffle(options)
        st.session_state.test_options = options

def update_stat(word, is_correct):
    if word not in st.session_state.stats:
        st.session_state.stats[word] = {"correct": 0, "wrong": 0}
    if is_correct: st.session_state.stats[word]["correct"] += 1
    else: st.session_state.stats[word]["wrong"] += 1

def submit_mcq(option):
    st.session_state.test_answered = True
    current_w = st.session_state.test_queue[st.session_state.test_q_count]
    if option == st.session_state.words[current_w]:
        st.session_state.test_score += 1
        st.session_state.test_msg = "⭕ 정답입니다!"
        update_stat(current_w, True)
    else:
        st.session_state.test_msg = f"❌ 오답입니다! (정답: {st.session_state.words[current_w]})"
        update_stat(current_w, False)

def submit_spell(user_text):
    st.session_state.test_answered = True
    current_w = st.session_state.test_queue[st.session_state.test_q_count]
    if user_text.strip().lower() == current_w.lower():
        st.session_state.test_score += 1
        st.session_state.test_msg = "⭕ 완벽해요!"
        update_stat(current_w, True)
    else:
        st.session_state.test_msg = f"❌ 틀렸습니다! (스펠링: {current_w})"
        update_stat(current_w, False)

# ==========================================
# 📱 사이드바
# ==========================================
with st.sidebar:
    st.header("🗂️ 시트 관리")
    new_sheet_name = st.text_input("새 시트 이름 추가", placeholder="예: 토익단어")
    col_add, col_del = st.columns(2)
    with col_add:
        if st.button("➕ 저장", use_container_width=True):
            if new_sheet_name and new_sheet_name not in st.session_state.saved_sheets:
                st.session_state.saved_sheets.append(new_sheet_name); st.rerun()
    with col_del:
        if st.button("🗑️ 삭제", use_container_width=True):
            if new_sheet_name in st.session_state.saved_sheets:
                st.session_state.saved_sheets.remove(new_sheet_name); st.rerun()

    st.divider()
    selected_sheets = st.multiselect("📂 불러올 시트 선택", options=st.session_state.saved_sheets, default=st.session_state.saved_sheets[:1])
    if st.button("🚀 데이터 불러오기", type="primary", use_container_width=True):
        if selected_sheets:
            with st.spinner("데이터 병합 중..."):
                try:
                    w, n, s = google_db.load_multiple_sheets(selected_sheets)
                    st.session_state.words, st.session_state.notes, st.session_state.stats = w, n, s
                    st.session_state.word_list = list(w.keys())
                    st.session_state.current_idx, st.session_state.current_sheet = 0, selected_sheets[0]
                    st.session_state.test_active = False
                    st.success(f"총 {len(w)}개의 단어 로드 완료!")
                except: st.error("시트 로드 실패!")

    st.divider()
    st.write("🔄 카드 방향 설정")
    direction = st.radio("방향", ["단어 ➔ 뜻", "뜻 ➔ 단어"], label_visibility="collapsed")
    st.session_state.direction = "W2M" if direction == "단어 ➔ 뜻" else "M2W"

    st.divider()
    st.header("🔐 관리자 모드")
    admin_pw = st.text_input("비밀번호", type="password")
    if admin_pw == st.secrets["admin_password"]: st.session_state.is_admin = True
    else: st.session_state.is_admin = False

# ==========================================
# 📱 메인 화면
# ==========================================
st.title("📖 Veha's English Web")

if not st.session_state.word_list:
    st.info("👈 왼쪽 사이드바에서 시트를 선택하고 '데이터 불러오기'를 눌러주세요!")
else:
    tab_list, tab_study, tab_test, tab_stats = st.tabs(["📋 단어 목록", "📖 기본 학습", "📝 시험 모드", "📊 현황판"])

    # --- [탭 1] 단어 목록 ---
    with tab_list:
        if st.session_state.is_admin:
            with st.expander("➕ 단어 즉시 등록 (관리자 전용)", expanded=False):
                with st.form("add_word_form", clear_on_submit=True):
                    col1, col2, col3 = st.columns([2, 2, 3])
                    new_word, new_mean, new_note = col1.text_input("단어*"), col2.text_input("뜻*"), col3.text_input("부가설명")
                    if st.form_submit_button("구글 시트에 쏘기! 🚀"):
                        if new_word and new_mean:
                            google_db.add_word_to_sheet(st.session_state.current_sheet, new_word, new_mean, new_note)
                            st.success(f"'{new_word}' 등록 완료!")
            st.divider()

        # 🎯 수정된 부분: 단어 리스트 출력 (아이콘 및 포스트잇 기능)
        for w in st.session_state.word_list:
            mean = st.session_state.words[w]
            note = st.session_state.notes.get(w, "").strip()
            
            with st.container(border=True):
                # 단어:노트아이콘:오디오아이콘 순서로 배치 (비율 7:1.5:1.5)
                cols = st.columns([0.7, 0.15, 0.15])
                
                # 1. 단어와 뜻
                cols[0].markdown(f"**{w}** : {mean}")
                
                # 2. 부가설명 아이콘 (노트가 있을 때만 나타남)
                with cols[1]:
                    if note:
                        # 클릭 시 포스트잇처럼 뜨는 팝오버 창
                        with st.popover("💡", help="부가설명 확인"):
                            st.info(note) # 파란색 박스로 포스트잇 느낌 강조
                
                # 3. 발음 버튼
                if cols[2].button("🔊", key=f"audio_{w}", use_container_width=True):
                    st.audio(get_audio_player(w), format="audio/mp3", autoplay=True)
                
                # 관리자 전용 수정/삭제 (아래쪽에 배치)
                if st.session_state.is_admin:
                    with st.expander("⚙️ 수정/삭제"):
                        edit_col1, edit_col2 = st.columns(2)
                        with edit_col1:
                            new_w = st.text_input("단어", value=w, key=f"ew_{w}")
                            new_m = st.text_input("뜻", value=mean, key=f"em_{w}")
                            new_n = st.text_input("설명", value=note, key=f"en_{w}")
                            if st.button("💾 저장", key=f"btn_e_{w}"):
                                google_db.edit_word_in_sheet(st.session_state.current_sheet, w, new_w, new_m, new_n); st.success("수정됨!")
                        with edit_col2:
                            if st.button("🗑️ 삭제", key=f"btn_d_{w}", type="primary"):
                                google_db.delete_word_from_sheet(st.session_state.current_sheet, w); st.error("삭제됨")

    # [나머지 학습/시험/현황판 탭 코드는 이전과 동일하게 유지]
    # --- [탭 2] 기본 학습 ---
    with tab_study:
        current_word = st.session_state.word_list[st.session_state.current_idx]
        mean = st.session_state.words[current_word]
        note = st.session_state.notes.get(current_word, "")
        is_w2m = (st.session_state.direction == "W2M")
        front_text, front_color = (current_word, "#2980B9") if not st.session_state.show_meaning else (mean, "#D35400")
        if not is_w2m: front_text, front_color = (mean, "#2980B9") if not st.session_state.show_meaning else (current_word, "#D35400")

        st.markdown(f'<div style="background-color: #f0f2f6; border-radius: 15px; padding: 40px; text-align: center; border: 3px solid {front_color};"><h1 style="color: {front_color}; font-size: 2.5rem; margin: 0;">{front_text}</h1></div><br>', unsafe_allow_html=True)
        if note and st.session_state.show_meaning: st.info(f"💡 {note}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 뒤집기", use_container_width=True): st.session_state.show_meaning = not st.session_state.show_meaning; st.rerun()
        with col2:
            if st.button("➡️ 다음 단어", use_container_width=True, type="primary"):
                st.session_state.current_idx = (st.session_state.current_idx + 1) % len(st.session_state.word_list)
                st.session_state.show_meaning = False; st.rerun()
        if st.button("🔊 발음 듣기", use_container_width=True): st.audio(get_audio_player(current_word), format="audio/mp3", autoplay=True)

    # --- [탭 3] 시험 모드 ---
    with tab_test:
        if not st.session_state.test_active:
            st.subheader("🎯 시험 설정")
            test_type = st.selectbox("시험 방식", ["객관식", "스펠링"])
            max_q = len(st.session_state.word_list)
            q_count = st.number_input(f"문제 수 (최대 {max_q}개)", min_value=1, max_value=max_q, value=min(10, max_q))
            if st.button("🚀 시작", type="primary", use_container_width=True):
                st.session_state.test_active, st.session_state.test_type, st.session_state.test_q_max = True, test_type, q_count
                st.session_state.test_q_count, st.session_state.test_score = 0, 0
                pool = list(st.session_state.word_list); random.shuffle(pool); st.session_state.test_queue = pool[:q_count]
                prepare_question(); st.rerun()
        else:
            st.progress(st.session_state.test_q_count / st.session_state.test_q_max)
            current_w = st.session_state.test_queue[st.session_state.test_q_count]
            if st.session_state.test_type == "객관식":
                st.markdown(f"<h2 style='text-align: center;'>{current_w}</h2>", unsafe_allow_html=True)
                if not st.session_state.test_answered:
                    for opt in st.session_state.test_options:
                        if st.button(opt, use_container_width=True): submit_mcq(opt); st.rerun()
            else:
                st.markdown(f"<h2 style='text-align: center;'>{st.session_state.words[current_w]}</h2>", unsafe_allow_html=True)
                if not st.session_state.test_answered:
                    with st.form(f"f_{st.session_state.test_q_count}"):
                        u = st.text_input("영어 입력:"); 
                        if st.form_submit_button("확인"): submit_spell(u); st.rerun()
            if st.session_state.test_answered:
                st.success(st.session_state.test_msg) if "⭕" in st.session_state.test_msg else st.error(st.session_state.test_msg)
                st.audio(get_audio_player(current_w), format="audio/mp3", autoplay=True)
                if st.session_state.test_q_count < st.session_state.test_q_max - 1:
                    if st.button("다음 ➡️"): st.session_state.test_q_count += 1; prepare_question(); st.rerun()
                else:
                    st.info(f"종료! 점수: {st.session_state.test_score}/{st.session_state.test_q_max}")
                    if st.button("저장 💾"): google_db.save_stats(st.session_state.current_sheet, st.session_state.stats); st.session_state.test_active = False; st.rerun()

    # --- [탭 4] 현황판 ---
    with tab_stats:
        st.subheader("📊 현황")
        if st.session_state.stats:
            for w, data in sorted(st.session_state.stats.items(), key=lambda x: x[1]['wrong'], reverse=True):
                with st.container(border=True):
                    st.write(f"**{w}** : {st.session_state.words.get(w, '')}")
                    st.markdown(f"⭕ {data['correct']} | ❌ {data['wrong']}")
        else: st.info("통계 없음")
