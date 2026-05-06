import streamlit as st
import google_db
from gtts import gTTS
import io
import random
import base64
import time
import streamlit.components.v1 as components

# 1. 브라우저 설정
st.set_page_config(page_title="Veha's English", page_icon="📖", layout="centered")

# 🎯 모바일 화면 가로 스크롤 완전 차단 및 잔상 제거 CSS
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"], .main {
        overflow-x: hidden !important;
        max-width: 100vw !important;
    }
    .main-title {
        font-size: clamp(1.4rem, 6vw, 2.5rem);
        font-weight: 800;
        margin-bottom: 1rem;
        padding-top: 1rem;
    }
    .stButton>button {
        border-radius: 10px;
        min-height: 2.8rem;
        height: auto !important;
        white-space: normal !important; 
        text-align: left !important;
        word-break: break-word !important; 
    }
    .stPopover > button {
        border-radius: 10px !important;
        border: 1px dashed #f39c12 !important;
        color: #d35400 !important;
        background-color: #fdfae6 !important;
    }
    /* 선택지 등이 사라질 때 흐려지는 효과(잔상)를 강제 삭제하여 즉시 증발시킴 */
    .element-container, [data-testid="stElementContainer"] {
        transition: none !important;
        animation: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 앱의 기억력 세팅
if 'word_list' not in st.session_state:
    st.session_state.words = {}
    st.session_state.notes = {}
    st.session_state.word_list = []
    st.session_state.current_idx = 0
    st.session_state.show_meaning = False
    st.session_state.is_admin = False
    st.session_state.current_sheet = ""
    st.session_state.stats = {}
    st.session_state.saved_sheets = ["영어"]
    st.session_state.card_direction = "단어 ➔ 뜻" 
    
    st.session_state.test_active = False
    st.session_state.test_type = "객관식"
    st.session_state.test_q_max = 0
    st.session_state.test_q_count = 0
    st.session_state.test_queue = []
    st.session_state.test_score = 0
    st.session_state.test_answered = False
    st.session_state.test_options = []
    st.session_state.test_msg = ""
    st.session_state.auto_advance = False 
    
if 'play_audio_b64' not in st.session_state:
    st.session_state.play_audio_b64 = None
if 'play_audio_key' not in st.session_state:
    st.session_state.play_audio_key = "init"

# 🎯 [버그 해결] 음성 무한 반복 재생 조수
def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    st.session_state.play_audio_b64 = base64.b64encode(fp.read()).decode()
    # 똑같은 버튼을 눌러도 무조건 재생되도록 고유 번호(시간)를 강제로 부여!
    st.session_state.play_audio_key = f"audio_{time.time()}"

# 거대 플래시카드 버튼 조수
def render_giant_button(text, hint, color, key):
    st.markdown(f"""
    <div id="anchor-{key}"></div>
    <style>
    div[data-testid="element-container"]:has(#anchor-{key}) + div[data-testid="element-container"] button,
    div.element-container:has(#anchor-{key}) + div.element-container button {{
        height: 220px !important;
        border: 3px solid {color} !important;
        border-radius: 15px !important;
        background-color: #f0f2f6 !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
        transition: transform 0.1s ease !important;
    }}
    div[data-testid="element-container"]:has(#anchor-{key}) + div[data-testid="element-container"] button:active,
    div.element-container:has(#anchor-{key}) + div.element-container button:active {{
        transform: scale(0.97) !important;
    }}
    div[data-testid="element-container"]:has(#anchor-{key}) + div[data-testid="element-container"] button p:nth-of-type(1),
    div.element-container:has(#anchor-{key}) + div.element-container button p:nth-of-type(1) {{
        font-size: clamp(2rem, 8vw, 2.8rem) !important;
        font-weight: bold !important;
        color: {color} !important;
        margin: 0 !important;
        text-align: center !important;
        width: 100% !important;
    }}
    div[data-testid="element-container"]:has(#anchor-{key}) + div[data-testid="element-container"] button p:nth-of-type(2),
    div.element-container:has(#anchor-{key}) + div.element-container button p:nth-of-type(2) {{
        font-size: 0.9rem !important;
        color: #7f8c8d !important;
        margin-top: 15px !important;
        text-align: center !important;
        width: 100% !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    return st.button(f"{text}\n\n{hint}", key=key, use_container_width=True)

# --- 시험 및 통계 로직 ---
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
    st.radio("방향", ["단어 ➔ 뜻", "뜻 ➔ 단어"], key="card_direction", label_visibility="collapsed")

    st.divider()
    st.header("🔐 관리자 모드")
    admin_pw = st.text_input("비밀번호", type="password")
    st.session_state.is_admin = (admin_pw == st.secrets["admin_password"])

# ==========================================
# 📱 메인 화면
# ==========================================
st.markdown('<div class="main-title">📖 Veha\'s English Web</div>', unsafe_allow_html=True)

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
                if note:
                    with st.popover("💡 부가설명 보기", use_container_width=True): st.info(note)
                
                if st.button(f"**{w}** : {mean}", key=f"btn_w_{w}", use_container_width=True):
                    play_audio(w) 
                
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
        is_w2m = (st.session_state.card_direction == "단어 ➔ 뜻")
        
        front_text, front_color = (current_word, "#2980B9") if not st.session_state.show_meaning else (mean, "#D35400")
        if not is_w2m: front_text, front_color = (mean, "#2980B9") if not st.session_state.show_meaning else (current_word, "#D35400")

        # 🎯 [수정] 카드 클릭 = 뒤집기 + 소리 동시 발동! 
        if render_giant_button(front_text, "👆 클릭하여 뒤집고 발음 듣기", front_color, "main_card_btn"):
            play_audio(current_word) 
            st.session_state.show_meaning = not st.session_state.show_meaning 
            st.rerun()
        
        if note and st.session_state.show_meaning: st.info(f"💡 {note}")
        
        # 🎯 [수정] 하단에 자리만 차지하던 발음 듣기 버튼 삭제! 깔끔하게 '다음 단어'만 남김
        if st.button("➡️ 다음 단어", use_container_width=True, type="primary"):
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
            col_prog, col_stop = st.columns([7, 3])
            with col_prog:
                st.progress(st.session_state.test_q_count / st.session_state.test_q_max)
                st.caption(f"문제: {st.session_state.test_q_count + 1} / {st.session_state.test_q_max} (점수: {st.session_state.test_score})")
            
            with col_stop:
                if st.button("⏹️ 중단", use_container_width=True):
                    st.session_state.test_active = False; st.rerun()
            
            current_w = st.session_state.test_queue[st.session_state.test_q_count]
            
            if st.session_state.test_type == "객관식":
                if render_giant_button(current_w, "🔊 클릭하여 발음 듣기", "#2C3E50", "test_card_obj"):
                    play_audio(current_w)
                
                # 🎯 [버그 해결] 정답을 누르는 순간 선택지가 담긴 '빈 상자(st.empty)'를 완전히 파괴해버립니다!
                mcq_box = st.empty()
                if not st.session_state.test_answered:
                    with mcq_box.container():
                        for opt in st.session_state.test_options:
                            if st.button(opt, use_container_width=True): submit_mcq(opt); st.rerun()
                else:
                    mcq_box.empty() # 흔적도 없이 증발
            else:
                if render_giant_button(st.session_state.words[current_w], "아래에 영단어를 적어주세요", "#2C3E50", "test_card_spl"):
                    pass 
                
                spl_box = st.empty()
                if not st.session_state.test_answered:
                    with spl_box.container():
                        with st.form(f"f_{st.session_state.test_q_count}"):
                            u = st.text_input("영어 입력:"); 
                            if st.form_submit_button("확인"): submit_spell(u); st.rerun()
                else:
                    spl_box.empty() # 제출 즉시 폼 증발
            
            if st.session_state.test_answered:
                if "⭕" in st.session_state.test_msg:
                    st.success(st.session_state.test_msg)
                else:
                    st.error(st.session_state.test_msg)
                    
                play_audio(current_w)
                
                if st.session_state.test_q_count < st.session_state.test_q_max - 1:
                    st.caption("⏳ 잠시 후 자동으로 넘어갑니다...")
                    st.session_state.auto_advance = True
                else:
                    st.info(f"🎉 종료! 점수: {st.session_state.test_score}/{st.session_state.test_q_max}")
                    if st.button("저장 💾"): google_db.save_stats(st.session_state.current_sheet, st.session_state.stats); st.session_state.test_active = False; st.rerun()

    # --- [탭 4] 현황판 ---
    with tab_stats:
        if st.session_state.stats:
            for w, d in sorted(st.session_state.stats.items(), key=lambda x: x[1]['wrong'], reverse=True):
                with st.container(border=True):
                    st.write(f"**{w}** : {st.session_state.words.get(w, '')}")
                    st.caption(f"⭕ {d['correct']} | ❌ {d['wrong']}")

# 🎯 [버그 해결] 타임스탬프 키(key)를 적용하여 클릭할 때마다 강제로 무한 반복 재생!
if st.session_state.play_audio_b64:
    html = f"""<audio autoplay="true"><source src="data:audio/mp3;base64,{st.session_state.play_audio_b64}" type="audio/mp3"></audio>"""
    components.html(html, width=0, height=0, key=st.session_state.play_audio_key)
    st.session_state.play_audio_b64 = None

# 자동 넘김 딜레이
if st.session_state.auto_advance:
    st.session_state.auto_advance = False
    time.sleep(1.5) 
    st.session_state.test_q_count += 1
    prepare_question()
    st.rerun()
