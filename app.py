import streamlit as st

# 1. 브라우저 탭 설정
st.set_page_config(page_title="Veha's English", page_icon="📖", layout="centered")

# 2. 메인 타이틀
st.title("📖 Veha's English Web")
st.write("모바일 웹 버전 테스트 화면입니다! 곧 구글 시트와 연결됩니다.")

# 3. 임시 단어 데이터 (나중에 구글 시트 데이터로 교체될 부분)
words = {"Apple": "사과", "Banana": "바나나", "Computer": "컴퓨터", "Developer": "개발자"}
word_list = list(words.keys())

# 4. 앱의 기억력(세션 상태) 세팅
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'show_meaning' not in st.session_state:
    st.session_state.show_meaning = False

current_word = word_list[st.session_state.current_index]

# 5. 플래시카드 화면 UI (PC/모바일 반응형)
st.markdown("---")
if not st.session_state.show_meaning:
    # 앞면 (단어)
    st.markdown(f"<h1 style='text-align: center; color: #2980B9; font-size: 50px;'>{current_word}</h1>", unsafe_allow_html=True)
else:
    # 뒷면 (뜻)
    st.markdown(f"<h1 style='text-align: center; color: #D35400; font-size: 40px;'>{words[current_word]}</h1>", unsafe_allow_html=True)
st.markdown("---")

# 6. 모바일 친화적인 버튼 (가로로 꽉 차게 2칸 분할)
col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 뒤집기", use_container_width=True):
        st.session_state.show_meaning = not st.session_state.show_meaning
        st.rerun() # 화면 새로고침
with col2:
    if st.button("➡️ 다음 단어", use_container_width=True):
        st.session_state.current_index = (st.session_state.current_index + 1) % len(word_list)
        st.session_state.show_meaning = False # 다음 단어로 갈 땐 무조건 앞면
        st.rerun()
