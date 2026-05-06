import streamlit as st
import google_db
from gtts import gTTS
import io

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
    st.session_state.is_admin = False # 🎯 관리자 로그인 여부 기억
    st.session_state.current_sheet = "" # 🎯 현재 열려있는 시트 이름 기억

def get_audio_player(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp

# ==========================================
# 📱 사이드바 (서랍 메뉴)
# ==========================================
with st.sidebar:
    st.header("⚙️ 설정 및 로드")
    sheet_input = st.text_input("구글 시트 이름 입력", placeholder="예: 영어")
    
    if st.button("데이터 불러오기", type="primary", use_container_width=True):
        if sheet_input:
            with st.spinner("구글 시트에서 가져오는 중..."):
                try:
                    w, n = google_db.load_words_from_sheet(sheet_input)
                    st.session_state.words = w
                    st.session_state.notes = n
                    st.session_state.word_list = list(w.keys())
                    st.session_state.current_idx = 0
                    st.session_state.current_sheet = sheet_input # 시트 이름 저장
                    st.success(f"성공! 총 {len(w)}개의 단어 로드 완료.")
                except Exception as e:
                    st.error("시트를 찾을 수 없거나 권한이 없습니다.")
        else:
            st.warning("시트 이름을 적어주세요.")

    st.divider()
    st.write("🔄 카드 방향 설정")
    direction = st.radio("방향", ["단어 ➔ 뜻", "뜻 ➔ 단어"], label_visibility="collapsed")
    st.session_state.direction = "W2M" if direction == "단어 ➔ 뜻" else "M2W"

    # 🔐 관리자 로그인 메뉴
    st.divider()
    st.header("🔐 관리자 모드")
    admin_pw = st.text_input("비밀번호를 입력하세요", type="password")
    
    if admin_pw:
        if admin_pw == st.secrets["admin_password"]:
            st.session_state.is_admin = True
            st.success("✅ 관리자 인증 완료!")
        else:
            st.session_state.is_admin = False
            st.error("❌ 비밀번호가 다릅니다.")

# ==========================================
# 📱 메인 화면
# ==========================================
st.title("📖 Veha's English Web")

if not st.session_state.word_list:
    st.info("👈 화면 왼쪽 위 `>` 버튼을 눌러 사이드바를 열고, 구글 시트를 먼저 불러와주세요!")
else:
    tab_list, tab_study = st.tabs(["📋 단어 목록", "📖 기본 학습"])

    # --- [탭 1] 단어 목록 ---
    with tab_list:
        
        # 🎯 관리자 모드일 때만 '단어 즉시 등록' 메뉴가 보입니다!
        if st.session_state.is_admin:
            with st.expander("➕ 단어 즉시 등록 (관리자 전용)", expanded=False):
                with st.form("add_word_form", clear_on_submit=True):
                    st.caption(f"현재 등록될 시트: **{st.session_state.current_sheet}**")
                    col1, col2, col3 = st.columns([2, 2, 3])
                    new_word = col1.text_input("단어*")
                    new_mean = col2.text_input("뜻*")
                    new_note = col3.text_input("부가설명 (선택)")
                    
                    submitted = st.form_submit_button("구글 시트에 쏘기! 🚀")
                    
                    if submitted:
                        if new_word and new_mean:
                            with st.spinner("시트에 기록 중..."):
                                google_db.add_word_to_sheet(st.session_state.current_sheet, new_word, new_mean, new_note)
                                st.success(f"'{new_word}' 등록 완료! (화면에 반영하려면 좌측에서 데이터를 다시 불러와주세요)")
                        else:
                            st.warning("단어와 뜻은 필수 입력입니다.")
            st.divider()

        # 기존 단어 리스트 출력
        for w in st.session_state.word_list:
            mean = st.session_state.words[w]
            note = st.session_state.notes.get(w, "")
            
            with st.container(border=True):
                cols = st.columns([4, 1])
                cols[0].write(f"**{w}** : {mean}")
                if note:
                    cols[0].caption(f"📝 {note}")
                
                if cols[1].button("🔊", key=f"audio_{w}"):
                    st.audio(get_audio_player(w), format="audio/mp3", autoplay=True)

    # --- [탭 2] 기본 학습 ---
    with tab_study:
        current_word = st.session_state.word_list[st.session_state.current_idx]
        mean = st.session_state.words[current_word]
        note = st.session_state.notes.get(current_word, "")
        is_w2m = (st.session_state.direction == "W2M")
        
        if not st.session_state.show_meaning:
            front_text = current_word if is_w2m else mean
            front_color = "#2980B9"
        else:
            front_text = mean if is_w2m else current_word
            front_color = "#D35400"

        st.markdown(f"""
        <div style="background-color: #f0f2f6; border-radius: 15px; padding: 40px; text-align: center; border: 3px solid {front_color};">
            <h1 style="color: {front_color}; font-size: 2.5rem; margin: 0;">{front_text}</h1>
        </div>
        <br>
        """, unsafe_allow_html=True)

        if note and st.session_state.show_meaning:
            st.info(f"💡 {note}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 뒤집기", use_container_width=True):
                st.session_state.show_meaning = not st.session_state.show_meaning
                st.rerun()
        with col2:
            if st.button("➡️ 다음 단어", use_container_width=True, type="primary"):
                st.session_state.current_idx = (st.session_state.current_idx + 1) % len(st.session_state.word_list)
                st.session_state.show_meaning = False
                st.rerun()

        st.divider()
        if st.button("🔊 현재 단어 발음 듣기", use_container_width=True):
            st.audio(get_audio_player(current_word), format="audio/mp3", autoplay=True)
