import streamlit as st
import google_db
from gtts import gTTS
import io
import random
import base64
import streamlit.components.v1 as components

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
    
if 'play_audio_b64' not in st.session_state:
    st.session_state.play_audio_b64 = None

# 🎯 [수정] 단어 목록용 오디오 준비 (화면 맨 밑에서 재생되도록 기억만 해둠)
def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    st.session_state.play_audio_b64 = base64.b64encode(fp.read()).decode()

# 🎯 [수정] 크고 예쁜 클릭형 플래시카드 조수! (자바스크립트 즉시 재생)
def render_clickable_card(text, color, audio_text=None):
    b64_audio = ""
    if audio_text:
        tts = gTTS(text=audio_text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        b64_audio = base64.b64encode(fp.read()).decode()
        
    audio_tag = f'<audio id="card_audio" src="data:audio/mp3;base64,{b64_audio}"></audio>' if b64_audio else ""
    click_action = 'document.getElementById("card_audio").play()' if b64_audio else ""
    cursor = "pointer" if b64_audio else "default"
    hint_text = '<div class="hint">👆 클릭하여 발음 듣기</div>' if b64_audio else ''

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; background-color: transparent; }}
            .card {{
                cursor: {cursor};
                background-color: #f0f2f6;
                border-radius: 15px;
                padding: 20px;
                text-align: center;
                border: 3px solid {color};
                height: 220px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                box-sizing: border-box;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }}
            h1 {{ color: {color}; font-size: 2.8rem; margin: 0; font-weight: bold; }}
            .hint {{ color: #7f8c8d; font-size: 0.9rem; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="card" onclick='{click_action}'>
            <h1>{text}</h1>
            {hint_text}
            {audio_tag}
        </div>
    </body>
    </html>
    """
    components.html(html, height=240)

# --- 기능 조수 함수들 ---
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
    st.session_state.is_admin = (admin_pw == st.secrets["admin_password"])

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
            with st.expander("➕ 단어 즉시 등록"):
                with st.form("add_form", clear_on_submit=True):
                    col1, col2, col3 = st.columns(3)
                    w_i, m_i, n_i = col1.text_input("단어"), col2.text_input("뜻"), col3.text_input("설명")
                    if st.form_submit_button("등록"):
                        google_db.add_word_to_sheet(st.session_state.current_sheet, w_i, m_i, n_i); st.rerun()

        for w in st.session_state.word_list:
            mean = st.session_state.words[w]
            note = st.session_state.notes.get(w, "").strip()
            with st.container(border=True):
                cols = st.columns([0.85, 0.15])
                
                # 🎯 [수정] 누르면 소리가 나되, 덜컹거리지 않도록 로직 분리
                if cols[0].button(f"**{w}** : {mean}", key=f"btn_w_{w}", use_container_width=True):
                    play_audio(w) 
                
                with cols[1]:
                    if note:
                        with st.popover("💡"): st.info(note)
                
                if st.session_state.is_admin:
                    with st.expander("⚙️ 수정/삭제"):
                        new_w = st.text_input("단어", value=w, key=f"ew_{w}")
                        new_m = st.text_input("뜻", value=mean, key=f"em_{w}")
                        new_n = st.text_input("설명", value=note, key=f"en_{w}")
                        ec1, ec2 = st.columns(2)
                        if ec1.button("💾 저장", key=f"sv_{w}"):
                            google_db.edit_word_in_sheet(st.session_state.current_sheet, w, new_w, new_m, new_n); st.rerun()
                        if ec2.button("🗑️ 삭제", key=f"del_{w}", type="primary"):
                            google_db.delete_word_from_sheet(st.session_state.current_sheet, w); st.rerun()

    # --- [탭 2] 기본 학습 ---
    with tab_study:
        current_word = st.session_state.word_list[st.session_state.current_idx]
        mean = st.session_state.words[current_word]
        note = st.session_state.notes.get(current_word, "")
        is_w2m = (st.session_state.direction == "W2M")
        
        front_text, front_color = (current_word, "#2980B9") if not st.session_state.show_meaning else (mean, "#D35400")
        if not is_w2m: front_text, front_color = (mean, "#2980B9") if not st.session_state.show_meaning else (current_word, "#D35400")

        # 🎯 [수정] 예쁘고 크고 통통한 카드 복구! 누르면 즉시 재생됩니다.
        render_clickable_card(front_text, front_color, audio_text=current_word)
        
        if note and st.session_state.show_meaning: st.info(f"💡 {note}")
        
        col1, col2 = st.columns(2)
        if col1.button("🔄 뒤집기", use_container_width=True):
            st.session_state.show_meaning = not st.session_state.show_meaning; st.rerun()
        if col2.button("➡️ 다음 단어", use_container_width=True, type="primary"):
            st.session_state.current_idx = (st.session_state.current_idx + 1) % len(st.session_state.word_list)
            st.session_state.show_meaning = False; st.rerun()

    # --- [탭 3] 시험 모드 ---
    with tab_test:
        if not st.session_state.test_active:
            test_type = st.selectbox("시험 방식", ["객관식", "스펠링"])
            q_count = st.number_input("문제 수", min_value=1, value=min(10, len(st.session_state.word_list)))
            if st.button("🚀 시작", type="primary", use_container_width=True):
                st.session_state.test_active, st.session_state.test_type = True, test_type
                st.session_state.test_q_max, st.session_state.test_q_count, st.session_state.test_score = q_count, 0, 0
                pool = list(st.session_state.word_list); random.shuffle(pool); st.session_state.test_queue = pool[:q_count]
                prepare_question(); st.rerun()
        else:
            st.progress(st.session_state.test_q_count / st.session_state.test_q_max)
            current_w = st.session_state.test_queue[st.session_state.test_q_count]
            
            if st.session_state.test_type == "객관식":
                # 🎯 [수정] 객관식 문제도 예쁜 카드로 출력
                render_clickable_card(current_w, "#2C3E50", audio_text=current_w)
                
                if not st.session_state.test_answered:
                    for opt in st.session_state.test_options:
                        if st.button(opt, use_container_width=True): submit_mcq(opt); st.rerun()
            else:
                # 🎯 [수정] 스펠링 문제(한글)도 카드로 출력 (소리는 안 남)
                render_clickable_card(st.session_state.words[current_w], "#2C3E50")
                if not st.session_state.test_answered:
                    with st.form(f"f_{st.session_state.test_q_count}"):
                        u = st.text_input("영어 입력:"); 
                        if st.form_submit_button("확인"): submit_spell(u); st.rerun()
            
            if st.session_state.test_answered:
                st.success(st.session_state.test_msg) if "⭕" in st.session_state.test_msg else st.error(st.session_state.test_msg)
                
                # 🎯 정답 확인 시 자동 재생
                play_audio(current_w)
                
                if st.session_state.test_q_count < st.session_state.test_q_max - 1:
                    if st.button("다음 ➡️"): st.session_state.test_q_count += 1; prepare_question(); st.rerun()
                else:
                    st.info(f"종료! 점수: {st.session_state.test_score}/{st.session_state.test_q_max}")
                    if st.button("저장 💾"): google_db.save_stats(st.session_state.current_sheet, st.session_state.stats); st.session_state.test_active = False; st.rerun()

    # --- [탭 4] 현황판 ---
    with tab_stats:
        if st.session_state.stats:
            for w, d in sorted(st.session_state.stats.items(), key=lambda x: x[1]['wrong'], reverse=True):
                with st.container(border=True):
                    st.write(f"**{w}** : {st.session_state.words.get(w, '')}")
                    st.caption(f"⭕ {d['correct']} | ❌ {d['wrong']}")

# ==========================================
# 🎯 [핵심] 덜컹거림 완벽 차단 로직
# ==========================================
# 단어 목록 등에서 버튼을 눌렀을 때 생성된 오디오를, 화면 맨~~~ 밑바닥 보이지 않는 곳에서 재생합니다!
if st.session_state.play_audio_b64:
    html = f"""
    <audio autoplay="true">
        <source src="data:audio/mp3;base64,{st.session_state.play_audio_b64}" type="audio/mp3">
    </audio>
    """
    # width=0, height=0 이라서 화면에 아무런 영향을 주지 않습니다.
    components.html(html, width=0, height=0)
    st.session_state.play_audio_b64 = None
