import streamlit as st
import google_db
from gtts import gTTS
import io
import random
import base64
import time

# 1. 브라우저 설정
st.set_page_config(page_title="Veha's English", page_icon="📖", layout="centered")

# 🎯 [수정] 오디오 재생바 완벽 숨김 및 버튼 스타일 정리
st.markdown("""
    <style>
    .stButton>button {
        border-radius: 10px;
        margin-bottom: -5px;
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

# 🎯 [수정] 깜빡임 없이 무한대로 즉시 재생되는 오디오 조수!
def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    b64 = base64.b64encode(fp.read()).decode()
    unique_id = str(time.time()) # 매번 새로운 소리인 것처럼 브라우저 속이기!
    
    # 안 보이는 HTML 오디오 태그를 화면에 슬쩍 끼워 넣어서 즉시 재생시킵니다.
    html = f"""
    <div style="width:0px; height:0px; overflow:hidden;">
        <audio id="{unique_id}" autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

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
