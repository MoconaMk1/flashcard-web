import streamlit as st
import google_db
from gtts import gTTS
import io

# 1. 브라우저 설정
st.set_page_config(page_title="Veha's English", page_icon="📖", layout="centered")

# 2. 앱의 기억력 (세션 상태) 세팅
if 'word_list' not in st.session_state:
    st.session_state.words = {}
    st.session_state.notes = {}
    st.session_state.word_list = []
    st.session_state.current_idx = 0
    st.session_state.show_meaning = False
    st.session_state.direction = "W2M" # W2M: 단어->뜻, M2W: 뜻->단어

# 3. 오디오 생성 조수
def get_audio_player(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp

# ==========================================
# 📱 사이드바 (서랍 메뉴) 설정
# ==========================================
with st.sidebar:
    st.header("⚙️ 설정 및 로드")
    sheet_input = st.text_input("구글 시트 이름 입력", placeholder="예: 영어")
    
    if st.button("데이터 불러오기", type="primary", use_container_width=True):
        if sheet_input:
            with st.spinner("구글 시트에서 가져오는 중..."):
                try:
                    # 우리가 만든 google_db 직원에게 일 시키기!
                    w, n = google_db.load_words_from_sheet(sheet_input)
                    st.session_state.words = w
                    st.session_state.notes = n
                    st.session_state.word_list = list(w.keys())
                    st.session_state.current_idx = 0
                    st.success(f"성공! 총 {len(w)}개의 단어 로드 완료.")
                except Exception as e:
                    st.error("시트를 찾을 수 없거나 권한이 없습니다.")
        else:
            st.warning("시트 이름을 적어주세요.")

    st.divider()
    st.write("🔄 카드 방향 설정")
    direction = st.radio("방향", ["단어 ➔ 뜻", "뜻 ➔ 단어"], label_visibility="collapsed")
    st.session_state.direction = "W2M" if direction == "단어 ➔ 뜻" else "M2W"

# ==========================================
# 📱 메인 화면
# ==========================================
st.title("📖 Veha's English Web")

if not st.session_state.word_list:
    st.info("👈 화면 왼쪽 위 `>` 버튼을 눌러 사이드바를 열고, 구글 시트를 먼저 불러와주세요!")
else:
    # 탭 메뉴 만들기 (단어 목록 / 기본 학습)
    tab_list, tab_study = st.tabs(["📋 단어 목록", "📖 기본 학습"])

    # --- [탭 1] 단어 목록 ---
    with tab_list:
        for w in st.session_state.word_list:
            mean = st.session_state.words[w]
            note = st.session_state.notes.get(w, "")
            
            with st.container(border=True):
                cols = st.columns([4, 1])
                cols[0].write(f"**{w}** : {mean}")
                if note:
                    cols[0].caption(f"📝 {note}")
                
                # 발음 듣기 버튼
                if cols[1].button("🔊", key=f"audio_{w}"):
                    st.audio(get_audio_player(w), format="audio/mp3", autoplay=True)

    # --- [탭 2] 기본 학습 ---
    with tab_study:
        current_word = st.session_state.word_list[st.session_state.current_idx]
        mean = st.session_state.words[current_word]
        note = st.session_state.notes.get(current_word, "")

        is_w2m = (st.session_state.direction == "W2M")
        
        # 앞/뒷면 글자와 색상 판별
        if not st.session_state.show_meaning:
            front_text = current_word if is_w2m else mean
            front_color = "#2980B9" # 파란색
        else:
            front_text = mean if is_w2m else current_word
            front_color = "#D35400" # 주황색

        # 카드 UI 그리기 (HTML/CSS 활용)
        st.markdown(f"""
        <div style="background-color: #f0f2f6; border-radius: 15px; padding: 40px; text-align: center; border: 3px solid {front_color};">
            <h1 style="color: {front_color}; font-size: 2.5rem; margin: 0;">{front_text}</h1>
        </div>
        <br>
        """, unsafe_allow_html=True)

        # 뒷면일 때만 부가 설명 보이기
        if note and st.session_state.show_meaning:
            st.info(f"💡 {note}")

        # 컨트롤 버튼
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 뒤집기", use_container_width=True):
                st.session_state.show_meaning = not st.session_state.show_meaning
                st.rerun() # 화면 새로고침
        with col2:
            if st.button("➡️ 다음 단어", use_container_width=True, type="primary"):
                st.session_state.current_idx = (st.session_state.current_idx + 1) % len(st.session_state.word_list)
                st.session_state.show_meaning = False
                st.rerun()

        st.divider()
        if st.button("🔊 현재 단어 발음 듣기", use_container_width=True):
            st.audio(get_audio_player(current_word), format="audio/mp3", autoplay=True)
