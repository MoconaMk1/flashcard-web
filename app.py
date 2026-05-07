import streamlit as st
import google_db
from gtts import gTTS
import io
import random
import base64
import time
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# 1. 브라우저 설정
st.set_page_config(page_title="Veha's English", page_icon="📖", layout="centered")

# 🎯 모바일 화면 최적화 및 카드 크기 강제 고정 CSS
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
    /* 플래시카드 거대화 디자인 (최신 Streamlit 대응) */
    [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(.giant-card) button {
        height: 220px !important;
        border: 3px solid #2980B9 !important;
        border-radius: 15px !important;
        background-color: #f0f2f6 !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
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
    .element-container, [data-testid="stElementContainer"] {
        transition: none !important;
        animation: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 앱의 기억력 세팅
if 'username' not in st.session_state:
    st.session_state.username = None 
    
if 'word_list' not in st.session_state:
    st.session_state.words = {}
    st.session_state.notes = {}
    st.session_state.all_words = []
    st.session_state.due_words = []
    st.session_state.word_list = []
    st.session_state.current_idx = 0
    st.session_state.show_meaning = False
    st.session_state.is_admin = False
    st.session_state.current_sheet = ""
    st.session_state.stats = {}
    # 기본 시트 이름 설정
    st.session_state.saved_sheets = ["맛있는 초등 필수 영단어 01-02"]
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
    st.session_state.test_finished = False

if 'play_audio_b64' not in st.session_state:
    st.session_state.play_audio_b64 = None
if 'play_audio_key' not in st.session_state:
    st.session_state.play_audio_key = "init"

# 각종 함수
def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    st.session_state.play_audio_b64 = base64.b64encode(fp.read()).decode()
    st.session_state.play_audio_key = str(time.time())

def render_audio_player():
    if st.session_state.play_audio_b64:
        html = f"""<audio autoplay="true"><source src="data:audio/mp3;base64,{st.session_state.play_audio_b64}" type="audio/mp3"></audio>
        <div style='display:none;'>{st.session_state.play_audio_key}</div>"""
        components.html(html, width=0, height=0)
        st.session_state.play_audio_b64 = None

def render_giant_button(text, hint, color, key):
    # .giant-card 클래스를 넣어 CSS가 정확히 타겟팅하게 함
    st.markdown('<div class="giant-card"></div>', unsafe_allow_html=True)
    return st.button(f"{text}\n\n{hint}", key=key, use_container_width=True)

def calculate_next_review(level):
    intervals = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
    days = intervals.get(level, 60)
    next_date = datetime.now() + timedelta(days=days)
    return next_date.strftime("%Y-%m-%d")

def update_stat(word, is_correct):
    if word not in st.session_state.stats:
        st.session_state.stats[word] = {"correct": 0, "wrong": 0, "level": 0, "next_review": ""}
    st.session_state.stats[word].setdefault("level", 0)
    if is_correct:
        st.session_state.stats[word]["correct"] += 1
        st.session_state.stats[word]["level"] += 1
    else:
        st.session_state.stats[word]["wrong"] += 1
        st.session_state.stats[word]["level"] = 0
    st.session_state.stats[word]["next_review"] = calculate_next_review(st.session_state.stats[word]["level"])

def prepare_question():
    st.session_state.test_answered = False
    st.session_state.test_msg = ""
    current_w = st.session_state.test_queue[st.session_state.test_q_count]
    if st.session_state.test_type == "객관식":
        correct_m = st.session_state.words[current_w]
        pool_m = [st.session_state.words[w] for w in st.session_state.all_words if w != current_w]
        options = random.sample(pool_m, min(3, len(pool_m))) + [correct_m]
        random.shuffle(options)
        st.session_state.test_options = options

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
# 🛑 로그인 화면
# ==========================================
if not st.session_state.username:
    st.markdown('<div class="main-title" style="text-align:center;">📖 Veha\'s English Web</div>', unsafe_allow_html=True)
    with st.form("login_form"):
        user_input = st.text_input("사용자 이름 (본인의 통계 탭이 생성됩니다)", placeholder="이름 입력")
        if st.form_submit_button("🚀 학습 시작하기", use_container_width=True):
            if user_input.strip():
                st.session_state.username = user_input.strip()
                st.rerun()
            else: st.error("이름을 입력해주세요!")
    st.stop() 

# 🎯 자동 불러오기
if not st.session_state.all_words and st.session_state.saved_sheets:
    target = st.session_state.saved_sheets[0]
    w, n, s, err = google_db.load_multiple_sheets([target], st.session_state.username)
    if w:
        st.session_state.words, st.session_state.notes, st.session_state.stats = w, n, s
        st.session_state.all_words = list(w.keys())
        today = datetime.now().strftime("%Y-%m-%d")
        due = [word for word in st.session_state.all_words if not s.get(word, {}).get("next_review", "") or s.get(word, {}).get("next_review", "") <= today]
        st.session_state.due_words, st.session_state.word_list = due, (due if due else st.session_state.all_words)
        st.session_state.current_sheet = target
    elif err:
        st.error(err)

# ==========================================
# 📱 사이드바
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 **{st.session_state.username}**님")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.divider()
    new_sheet = st.text_input("시트 이름 추가", placeholder="정확한 파일명 입력")
    c1, c2 = st.columns(2)
    if c1.button("➕ 저장"):
        if new_sheet and new_sheet not in st.session_state.saved_sheets:
            st.session_state.saved_sheets.append(new_sheet); st.rerun()
    if c2.button("🗑️ 삭제"):
        if new_sheet in st.session_state.saved_sheets:
            st.session_state.saved_sheets.remove(new_sheet); st.rerun()
    st.divider()
    sel_sheets = st.multiselect("📂 시트 선택", options=st.session_state.saved_sheets, default=st.session_state.saved_sheets[:1])
    if st.button("🚀 데이터 불러오기", type="primary", use_container_width=True):
        if sel_sheets:
            w, n, s, err = google_db.load_multiple_sheets(sel_sheets, st.session_state.username)
            if w:
                st.session_state.words, st.session_state.notes, st.session_state.stats = w, n, s
                st.session_state.all_words = list(w.keys())
                today = datetime.now().strftime("%Y-%m-%d")
                due = [word for word in st.session_state.all_words if not s.get(word, {}).get("next_review", "") or s.get(word, {}).get("next_review", "") <= today]
                st.session_state.due_words, st.session_state.word_list = due, (due if due else st.session_state.all_words)
                st.session_state.current_idx, st.session_state.current_sheet = 0, sel_sheets[0]
                st.session_state.test_active = False; st.success("로드 완료!")
            elif err: st.error(err)
    st.divider()
    target = st.radio("학습 범위", ["오늘 복습 대상", "전체 단어장"], key="study_target")
    st.session_state.word_list = st.session_state.due_words if target == "오늘 복습 대상" else st.session_state.all_words
    st.radio("방향", ["단어 ➔ 뜻", "뜻 ➔ 단어"], key="card_direction")
    admin_pw = st.text_input("관리자 비번", type="password")
    st.session_state.is_admin = (admin_pw == st.secrets["admin_password"])

# ==========================================
# 📱 메인 화면
# ==========================================
@st.fragment
def tab_list_ui():
    if st.session_state.is_admin:
        with st.expander("➕ 단어 즉시 등록"):
            with st.form("add_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                wi, mi, ni = c1.text_input("단어"), c2.text_input("뜻"), c3.text_input("설명")
                if st.form_submit_button("등록"):
                    google_db.add_word_to_sheet(st.session_state.current_sheet, wi, mi, ni); st.rerun()
    for w in st.session_state.word_list:
        mean, note = st.session_state.words[w], st.session_state.notes.get(w, "").strip()
        with st.container(border=True):
            if note:
                with st.popover("💡 부가설명", use_container_width=True): st.info(note)
            if st.button(f"**{w}** : {mean}", key=f"bw_{w}", use_container_width=True): play_audio(w)
            if st.session_state.is_admin:
                with st.expander("⚙️ 수정"):
                    nw, nm, nn = st.text_input("단", value=w, key=f"ew_{w}"), st.text_input("뜻", value=mean, key=f"em_{w}"), st.text_input("설", value=note, key=f"en_{w}")
                    if st.button("💾 저장", key=f"sv_{w}"): google_db.edit_word_in_sheet(st.session_state.current_sheet, w, nw, nm, nn); st.rerun()
                    if st.button("🗑️ 삭제", key=f"del_{w}", type="primary"): google_db.delete_word_from_sheet(st.session_state.current_sheet, w); st.rerun()
    render_audio_player()

@st.fragment
def tab_study_ui():
    if not st.session_state.word_list: st.info("학습할 단어가 없습니다."); return
    current_word = st.session_state.word_list[st.session_state.current_idx]
    mean, note = st.session_state.words[current_word], st.session_state.notes.get(current_word, "")
    is_w2m = (st.session_state.card_direction == "단어 ➔ 뜻")
    front_text = current_word if not st.session_state.show_meaning else mean
    if not is_w2m: front_text = mean if not st.session_state.show_meaning else current_word
    
    if render_giant_button(front_text, "👆 클릭하여 뒤집기", "#2980B9", "m_card"):
        play_audio(current_word); st.session_state.show_meaning = not st.session_state.show_meaning; st.rerun()
    
    if note and st.session_state.show_meaning: st.info(f"💡 {note}")
    if st.button("➡️ 다음 단어", use_container_width=True, type="primary"):
        st.session_state.current_idx = (st.session_state.current_idx + 1) % len(st.session_state.word_list)
        st.session_state.show_meaning = False; st.rerun()
    render_audio_player()

@st.fragment
def tab_test_ui():
    if not st.session_state.test_active:
        st.session_state.test_finished = False
        test_type = st.selectbox("시험 방식", ["객관식", "스펠링"])
        q_count = st.number_input("문제 수", min_value=1, value=min(10, len(st.session_state.word_list)))
        if st.button("🚀 시작", type="primary", use_container_width=True):
            st.session_state.test_active, st.session_state.test_type = True, test_type
            st.session_state.test_q_max, st.session_state.test_q_count, st.session_state.test_score = q_count, 0, 0
            pool = list(st.session_state.word_list); random.shuffle(pool); st.session_state.test_queue = pool[:q_count]
            prepare_question(); st.rerun()
    elif st.session_state.test_finished:
        st.balloons(); st.success(f"🎉 시험 종료! 점수: {st.session_state.test_score}/{st.session_state.test_q_max}")
        if st.button("처음으로 돌아가기", use_container_width=True): st.session_state.test_active = False; st.rerun()
    else:
        cp, cs = st.columns([7, 3])
        cp.progress(st.session_state.test_q_count / st.session_state.test_q_max)
        if cs.button("⏹️ 중단"): st.session_state.test_active = False; st.rerun()
        
        current_w = st.session_state.test_queue[st.session_state.test_q_count]
        if st.session_state.test_type == "객관식":
            if render_giant_button(current_w, "🔊 발음 듣기", "#2C3E50", "to"): play_audio(current_w)
            mcq_box = st.empty()
            if not st.session_state.test_answered:
                with mcq_box.container():
                    for opt in st.session_state.test_options:
                        if st.button(opt, use_container_width=True, key=f"opt_{opt}_{st.session_state.test_q_count}"): submit_mcq(opt); st.rerun()
            else: mcq_box.empty()
        else:
            render_giant_button(st.session_state.words[current_w], "영단어를 입력하세요", "#2C3E50", "ts")
            sb = st.empty()
            if not st.session_state.test_answered:
                with sb.container():
                    with st.form(f"f_{st.session_state.test_q_count}"):
                        u = st.text_input("영어 입력:"); 
                        if st.form_submit_button("확인"): submit_spell(u); st.rerun()
            else: sb.empty()

        if st.session_state.test_answered:
            if "⭕" in st.session_state.test_msg: st.success(st.session_state.test_msg)
            else: st.error(st.session_state.test_msg)
            play_audio(current_w)
            if st.session_state.test_q_count < st.session_state.test_q_max - 1:
                st.session_state.auto_advance = True
            else:
                with st.spinner("자동 저장 중..."):
                    google_db.save_stats(st.session_state.current_sheet, st.session_state.stats, st.session_state.username)
                time.sleep(1.5); st.session_state.test_finished = True; st.rerun()

    render_audio_player()
    if st.session_state.auto_advance:
        st.session_state.auto_advance = False
        time.sleep(1.5); st.session_state.test_q_count += 1; prepare_question(); st.rerun()

# 렌더링 시작
st.markdown('<div class="main-title">📖 Veha\'s English Web</div>', unsafe_allow_html=True)
if not st.session_state.all_words:
    st.info("데이터를 불러오는 중입니다... 시트 이름을 확인해주세요.")
else:
    t1, t2, t3, t4 = st.tabs(["📋 목록", "📖 학습", "📝 시험", "📊 현황"])
    with t1: tab_list_ui()
    with t2: tab_study_ui()
    with t3: tab_test_ui()
    with t4:
        if st.session_state.stats:
            for w, d in sorted(st.session_state.stats.items(), key=lambda x: x[1]['wrong'], reverse=True):
                with st.container(border=True):
                    st.write(f"**{w}** : {st.session_state.words.get(w, '')}")
                    st.caption(f"⭕ {d.get('correct',0)} | ❌ {d.get('wrong',0)} &nbsp;&nbsp; 📈 Lv.{d.get('level',0)} &nbsp;&nbsp; 📅 복습: {d.get('next_review', '오늘')}")
