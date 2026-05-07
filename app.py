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
    /* 목록 탭 전용 버튼 (왼쪽 정렬) */
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
    html_str = f'<div id="anchor-{key}" class="giant-card-
