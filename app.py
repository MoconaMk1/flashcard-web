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

# 🎯 UI 및 디자인 세팅
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
        min-height: 2.5rem;
        height: auto !important;
        font-size: 0.95rem !important; 
        padding: 0.4rem 0.6rem !important; 
        white-space: nowrap !important; 
    }
    .list-btn button {
        justify-content: flex-start !important;
        text-align: left !important;
    }
    .stPopover > button {
        border-radius: 10px !important;
        border: 1px dashed #f39c12 !important;
        color: #d35400 !important;
        background-color: #fdfae6 !important;
    }
    [data-testid="stElementContainer"]:has(.giant-card-anchor) + [data-testid="stElementContainer"] button,
    .element-container:has(.giant-card-anchor) + .element-container button {
        height: 280px !important;
        border: 1px solid #e0e6ed !important;
        border-radius: 20px !important;
        background: linear-gradient(145deg, #ffffff, #f1f3f5) !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        box-shadow: 0 10px 20px rgba(0,0,0,0.08), 0 4px 6px rgba(0,0,0,0.04) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        white-space: normal !important;
    }
    [data-testid="stElementContainer"]:has(.giant-card-anchor) + [data-testid="stElementContainer"] button:active,
    .element-container:has(.giant-card-anchor) + .element-container button:active {
        transform: scale(0.97) translateY(4px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    }
    [data-testid="stElementContainer"]:has(.giant-card-anchor) + [data-testid="stElementContainer"] button p:nth-of-type(1),
    .element-container:has(.giant-card-anchor) + .element-container button p:nth-of-type(1) {
        font-size: clamp(2.5rem, 8vw, 3.5rem) !important;
        font-weight: 900 !important;
        margin: 0 !important;
    }
    [data-testid="stElementContainer"]:has(.giant-card-anchor) + [data-testid="stElementContainer"] button p:nth-of-type(2),
    .element-container:has(.giant-card-anchor) + .element-container button p:nth-of-type(2) {
        color: #888 !important;
        font-size: 1rem !important;
        margin-top: 15px !important;
    }
    .element-container, [data-testid="stElementContainer"] {
        transition: none !important;
        animation: none !important;
    }
    div[style*="opacity: 0"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 앱의 기억력 세팅 (초기값)
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
    st.session_state.saved_sheets = []
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

if 'study_target' not in st.session_state:
    st.session_state.study_target = "전체 단어 (오답 우선)"
if 'card_direction' not in st.session_state:
    st.session_state.card_direction = "단어 ➔ 뜻"
if 'play_audio_b64' not in st.session_state:
    st.session_state.play_audio_b64 = None
if 'play_audio_key' not in st.session_state:
    st.session_state.play_audio_key = "init"
# 노트북용 기억력
if 'notebook_content' not in st.session_state:
    st.session_state.notebook_content = ""

# ==========================================
# 🧠 핵심 조수 함수
# ==========================================
def get_sorted_full_list(all_words_list, stats_dict):
    def sort_key(w):
        stat = stats_dict.get(w, {})
        priority = 0 if stat.get("level", 0) == 0 and stat.get("wrong", 0) > 0 else 1
        return (priority, all_words_list.index(w))
    return sorted(all_words_list, key=sort_key)

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
    html_str = f'<div id="anchor-{key}" class="giant-card-anchor"></div><style>[data-testid="stElementContainer"]:has(#anchor-{key}) + [data-testid="stElementContainer"] button p:nth-of-type(1), .element-container:has(#anchor-{key}) + .element-container button p:nth-of-type(1) {{ color: {color} !important; }}</style>'
    st.markdown(html_str, unsafe_allow_html=True)
    return st.button(f"{text}\n\n{hint}", key=key, use_container_width=True)

def calculate_next_review(level):
    intervals = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
    days = intervals.get(level, 60)
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

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
        st.session_state.test_score += 1; st.session_state.test_msg = "⭕ 정답입니다!"; update_stat(current_w, True)
    else:
        st.session_state.test_msg = f"❌ 오답입니다! (정답: {st.session_state.words[current_w]})"; update_stat(current_w, False)

def submit_spell(user_text):
    st.session_state.test_answered = True
    current_w = st.session_state.test_queue[st.session_state.test_q_count]
    if user_text.strip().lower() == current_w.lower():
        st.session_state.test_score += 1; st.session_state.test_msg = "⭕ 완벽해요!"; update_stat(current_w, True)
    else:
        st.session_state.test_msg = f"❌ 틀렸습니다! (스펠링: {current_w})"; update_stat(current_w, False)

# ==========================================
# 🛑 로그인 화면
# ==========================================
if not st.session_state.username:
    st.markdown('<div class="main-title" style="text-align:center;">📖 Veha\'s English Web</div>', unsafe_allow_html=True)
    with st.form("login_form"):
        user_input = st.text_input("사용자 이름", placeholder="이름을 입력하세요")
        if st.form_submit_button("🚀 학습 시작하기", use_container_width=True):
            if user_input.strip():
                username = user_input.strip()
                st.session_state.username = username
                
                loaded_sheets = google_db.load_user_sheets(username)
                if isinstance(loaded_sheets, list):
                    if loaded_sheets:
                        st.session_state.saved_sheets = loaded_sheets
                    else:
                        st.session_state.saved_sheets = ["맛있는 초등 필수 영단어 01-02"]
                        google_db.save_user_sheets(username, st.session_state.saved_sheets)
                    
                    target, direction = google_db.load_user_settings(username)
                    st.session_state.study_target = target
                    st.session_state.card_direction = direction
                    
                    st.session_state.notebook_content = google_db.load_user_notebook(username)
                    
                    st.rerun() 
                else: st.error(f"⚠️ 설정 로드 실패: {loaded_sheets}"); st.stop()
            else: st.error("이름을 입력해주세요!")
    st.stop() 

# 자동 로드
if not st.session_state.all_words and st.session_state.saved_sheets:
    target = st.session_state.saved_sheets[0] 
    w, n, s, err = google_db.load_multiple_sheets([target], st.session_state.username)
    if w: 
        st.session_state.words, st.session_state.notes, st.session_state.stats = w, n, s
        st.session_state.all_words = list(w.keys())
        st.session_state.word_list = get_sorted_full_list(st.session_state.all_words, s)
        st.session_state.current_sheet = target

# ==========================================
# 📱 사이드바
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 **{st.session_state.username}**님")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.divider()

    st.header("🗂️ 내 단어장 관리")
    new_sheet = st.text_input("새 시트 추가", placeholder="파일명 입력")
    if st.button("➕ 목록에 추가", use_container_width=True):
        if new_sheet and new_sheet not in st.session_state.saved_sheets:
            st.session_state.saved_sheets.append(new_sheet)
            res = google_db.save_user_sheets(st.session_state.username, st.session_state.saved_sheets)
            if res is True: st.toast("✅ 목록 영구 저장 완료!"); time.sleep(0.5); st.rerun()
            else: st.session_state.saved_sheets.remove(new_sheet); st.error(f"저장 실패: {res}")
            
    st.write("---")
    st.write("✅ **시트 선택 및 정렬**")
    selected_for_action = []
    updated_order = {}
    for i, sheet in enumerate(st.session_state.saved_sheets):
        c1, c2 = st.columns([7, 3])
        chk = c1.checkbox(sheet, key=f"chk_{sheet}")
        if chk: selected_for_action.append(sheet)
        order = c2.number_input("순서", value=i+1, min_value=1, key=f"ord_{sheet}", label_visibility="collapsed")
        updated_order[sheet] = order

    c_load, c_del, c_sort = st.columns(3)
    if c_load.button("🚀 로드"):
        if selected_for_action:
            with st.spinner("단어 로드 중..."):
                w, n, s, err = google_db.load_multiple_sheets(selected_for_action, st.session_state.username)
                if w: 
                    st.session_state.words, st.session_state.notes, st.session_state.stats = w, n, s
                    st.session_state.all_words = list(w.keys())
                    st.session_state.word_list = get_sorted_full_list(st.session_state.all_words, s)
                    st.session_state.current_idx, st.session_state.current_sheet = 0, selected_for_action[0]
                    st.session_state.test_active = False 
                    st.success(f"전체 로드 완료!")
                elif err: st.error(err)
        else: st.warning("시트를 체크해주세요.")
            
    if c_del.button("🗑️ 삭제"):
        if selected_for_action:
            for sht in selected_for_action: st.session_state.saved_sheets.remove(sht)
            res = google_db.save_user_sheets(st.session_state.username, st.session_state.saved_sheets)
            if res is True: st.toast("✅ 삭제 완료!"); time.sleep(0.5); st.rerun()
            else: st.error(f"삭제 실패: {res}")

    if c_sort.button("↕️ 정렬"):
        st.session_state.saved_sheets.sort(key=lambda x: updated_order[x])
        res = google_db.save_user_sheets(st.session_state.username, st.session_state.saved_sheets)
        if res is True: st.toast("✅ 정렬 완료!"); time.sleep(0.5); st.rerun()
        else: st.error(f"정렬 실패: {res}")

    st.divider()
    
    def update_settings_callback():
        res = google_db.save_user_settings(st.session_state.username, st.session_state.study_target, st.session_state.card_direction)
        if res is not True: st.error(f"설정 저장 실패: {res}")

    st.radio("🎯 학습 범위 선택", ["전체 단어 (오답 우선)", "오늘 복습 대상만"], key="study_target", on_change=update_settings_callback)
    
    if st.session_state.study_target == "전체 단어 (오답 우선)":
        st.session_state.word_list = get_sorted_full_list(st.session_state.all_words, st.session_state.stats) if 'all_words' in st.session_state else []
    else:
        today_str = datetime.now().strftime("%Y-%m-%d")
        due = [word for word in st.session_state.all_words if not st.session_state.stats.get(word, {}).get("next_review", "") or st.session_state.stats.get(word, {}).get("next_review", "") <= today_str]
        st.session_state.word_list = get_sorted_full_list(due, st.session_state.stats) if 'all_words' in st.session_state else []

    if st.session_state.current_idx >= len(st.session_state.word_list) and len(st.session_state.word_list) > 0:
        st.session_state.current_idx = 0

    st.radio("🔄 카드 방향", ["단어 ➔ 뜻", "뜻 ➔ 단어"], key="card_direction", on_change=update_settings_callback)
    
    st.divider()
    admin_pw = st.text_input("🔐 관리자 비번", type="password")
    st.session_state.is_admin = (admin_pw == st.secrets["admin_password"])

# ==========================================
# 📱 메인 화면 렌더링
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
    
    st.caption(f"총 {len(st.session_state.word_list)}개의 단어가 나열되어 있습니다. (틀린 단어 우선 정렬)")
    st.divider()
    
    st.markdown('<div class="list-btn">', unsafe_allow_html=True)
    for w in st.session_state.word_list:
        mean, note = st.session_state.words[w], st.session_state.notes.get(w, "").strip()
        prefix = "⚠️ " if st.session_state.stats.get(w, {}).get("level", 0) == 0 and st.session_state.stats.get(w, {}).get("wrong", 0) > 0 else ""
        btn_text = f"{prefix}**{w}** &nbsp;&nbsp;|&nbsp;&nbsp; {mean}"
        
        if note:
            col1, col2 = st.columns([85, 15])
            with col1:
                if st.button(btn_text, key=f"bw_{w}", use_container_width=True): play_audio(w)
            with col2:
                with st.popover("💡", use_container_width=True): st.info(note)
        else:
            if st.button(btn_text, key=f"bw_{w}", use_container_width=True): play_audio(w)
            
        if st.session_state.is_admin:
            with st.expander("⚙️ 수정 / 삭제"):
                nw, nm, nn = st.text_input("단어", value=w, key=f"ew_{w}"), st.text_input("뜻", value=mean, key=f"em_{w}"), st.text_input("설명", value=note, key=f"en_{w}")
                cc1, cc2 = st.columns(2)
                if cc1.button("💾 저장", key=f"sv_{w}", use_container_width=True): google_db.edit_word_in_sheet(st.session_state.current_sheet, w, nw, nm, nn); st.rerun()
                if cc2.button("🗑️ 삭제", key=f"del_{w}", type="primary", use_container_width=True): google_db.delete_word_from_sheet(st.session_state.current_sheet, w); st.rerun()
        st.divider() 
    st.markdown('</div>', unsafe_allow_html=True)
    render_audio_player()

@st.fragment
def tab_study_ui():
    if not st.session_state.word_list: st.info("학습할 단어가 없습니다."); return
    current_word = st.session_state.word_list[st.session_state.current_idx]
    mean, note = st.session_state.words[current_word], st.session_state.notes.get(current_word, "")
    is_w2m = (st.session_state.card_direction == "단어 ➔ 뜻")
    front_text = current_word if not st.session_state.show_meaning else mean
    if not is_w2m: front_text = mean if not st.session_state.show_meaning else current_word
    
    if render_giant_button(front_text, f"{st.session_state.current_idx + 1} / {len(st.session_state.word_list)} 👆 뒤집기", "#2980B9", "m_card"):
        play_audio(current_word); st.session_state.show_meaning = not st.session_state.show_meaning; st.rerun()
    
    if note and st.session_state.show_meaning: st.info(f"💡 {note}")
    if st.button("➡️ 다음 단어", use_container_width=True, type="primary"):
        st.session_state.current_idx = (st.session_state.current_idx + 1) % len(st.session_state.word_list)
        st.session_state.show_meaning = False; st.rerun()
    render_audio_player()

@st.fragment
def tab_test_ui():
    if not st.session_state.word_list: st.info("시험을 볼 단어가 없습니다."); return
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

# 🎯 노트북 UI (마크다운 엔터 무시 버그 완벽 수정!)
@st.fragment
def tab_notebook_ui():
    st.header("📓 나만의 비밀 영어 노트")
    
    with st.expander("✍️ 노트 수정하기", expanded=not st.session_state.notebook_content):
        new_content = st.text_area("공부하다 궁금한 점이나 핵심 문법을 정리해 보세요.", 
                                   value=st.session_state.notebook_content, 
                                   height=400,
                                   help="여기에 적은 내용은 영구적으로 저장됩니다.")
        if st.button("💾 노트북 저장", use_container_width=True, type="primary"):
            res = google_db.save_user_notebook(st.session_state.username, new_content)
            if res is True:
                st.session_state.notebook_content = new_content
                st.success("노트가 안전하게 저장되었습니다!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error(f"저장 실패: {res}")
    
    if st.session_state.notebook_content:
        st.markdown("---")
        # 🎯 핵심: 엔터 한 번(\n)을 마크다운 줄바꿈 규칙(스페이스바 2개 + \n)으로 강제 변환!
        display_content = st.session_state.notebook_content.replace('\n', '  \n')
        st.markdown(display_content)
    else:
        st.info("아직 작성된 내용이 없습니다. 위 에디터에서 내용을 추가해 보세요!")

# 렌더링 시작
st.markdown('<div class="main-title">📖 Veha\'s English Web</div>', unsafe_allow_html=True)
if not st.session_state.all_words:
    st.info("데이터를 불러오는 중입니다... 시트 이름을 확인해주세요.")
else:
    t1, t2, t3, t4, t5 = st.tabs(["📋 목록", "📖 학습", "📝 시험", "📊 현황", "💻 노트북"])
    with t1: tab_list_ui()
    with t2: tab_study_ui()
    with t3: tab_test_ui()
    with t4:
        if st.session_state.stats:
            for w, d in sorted(st.session_state.stats.items(), key=lambda x: x[1]['wrong'], reverse=True):
                with st.container(border=True):
                    st.write(f"**{w}** : {st.session_state.words.get(w, '')}")
                    st.caption(f"⭕ {d.get('correct',0)} | ❌ {d.get('wrong',0)} &nbsp;&nbsp; 📈 Lv.{d.get('level',0)} &nbsp;&nbsp; 📅 복습: {d.get('next_review', '오늘')}")
    with t5: tab_notebook_ui()
