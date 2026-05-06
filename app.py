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
    st.session_state.stats = {} # 🎯 통계 데이터 기억 공간 추가!
    
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

# 🎯 오답/정답 시 통계 카운트 증가 기능 추가
def update_stat(word, is_correct):
    if word not in st.session_state.stats:
        st.session_state.stats[word] = {"correct": 0, "wrong": 0}
    if is_correct:
        st.session_state.stats[word]["correct"] += 1
    else:
        st.session_state.stats[word]["wrong"] += 1

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
# 📱 사이드바 (서랍 메뉴)
# ==========================================
with st.sidebar:
    st.header("⚙️ 설정 및 로드")
    sheet_input = st.text_input("구글 시트 이름 입력", placeholder="예: 영어")
    
    if st.button("데이터 불러오기", type="primary", use_container_width=True):
        if sheet_input:
            with st.spinner("단어와 통계를 가져오는 중..."):
                try:
                    w, n = google_db.load_words_from_sheet(sheet_input)
                    s_data = google_db.load_stats(sheet_input) # 🎯 통계 데이터도 같이 부르기
                    st.session_state.words = w
                    st.session_state.notes = n
                    st.session_state.word_list = list(w.keys())
                    st.session_state.stats = s_data
                    st.session_state.current_idx = 0
                    st.session_state.current_sheet = sheet_input
                    st.session_state.test_active = False
                    st.success(f"성공! 총 {len(w)}개의 단어 로드 완료.")
                except Exception as e:
                    st.error("시트를 찾을 수 없거나 권한이 없습니다.")
        else:
            st.warning("시트 이름을 적어주세요.")

    st.divider()
    st.write("🔄 카드 방향 설정 (기본 학습용)")
    direction = st.radio("방향", ["단어 ➔ 뜻", "뜻 ➔ 단어"], label_visibility="collapsed")
    st.session_state.direction = "W2M" if direction == "단어 ➔ 뜻" else "M2W"

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
    # 🎯 탭이 4개로 늘어났습니다! 현황판 추가!
    tab_list, tab_study, tab_test, tab_stats = st.tabs(["📋 단어 목록", "📖 기본 학습", "📝 시험 모드", "📊 현황판"])

    # --- [탭 1] 단어 목록 ---
    with tab_list:
        if st.session_state.is_admin:
            with st.expander("➕ 단어 즉시 등록 (관리자 전용)", expanded=False):
                with st.form("add_word_form", clear_on_submit=True):
                    col1, col2, col3 = st.columns([2, 2, 3])
                    new_word = col1.text_input("단어*")
                    new_mean = col2.text_input("뜻*")
                    new_note = col3.text_input("부가설명 (선택)")
                    submitted = st.form_submit_button("구글 시트에 쏘기! 🚀")
                    if submitted:
                        if new_word and new_mean:
                            with st.spinner("시트에 기록 중..."):
                                google_db.add_word_to_sheet(st.session_state.current_sheet, new_word, new_mean, new_note)
                                st.success(f"'{new_word}' 등록 완료! (좌측 서랍에서 다시 불러와주세요)")
                        else:
                            st.warning("단어와 뜻은 필수입니다.")
            st.divider()

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
                
                if st.session_state.is_admin:
                    with st.expander("⚙️ 단어 수정/삭제"):
                        edit_col1, edit_col2 = st.columns(2)
                        with edit_col1:
                            new_w = st.text_input("단어 변경", value=w, key=f"ew_{w}")
                            new_m = st.text_input("뜻 변경", value=mean, key=f"em_{w}")
                            new_n = st.text_input("설명 변경", value=note, key=f"en_{w}")
                            if st.button("💾 수정 저장", key=f"btn_e_{w}"):
                                with st.spinner("수정 중..."):
                                    google_db.edit_word_in_sheet(st.session_state.current_sheet, w, new_w, new_m, new_n)
                                    st.success("완료! 다시 불러오기를 눌러주세요.")
                        with edit_col2:
                            st.write(" ")
                            st.write(" ")
                            if st.button("🗑️ 이 단어 삭제", key=f"btn_d_{w}", type="primary"):
                                with st.spinner("삭제 중..."):
                                    google_db.delete_word_from_sheet(st.session_state.current_sheet, w)
                                    st.error("삭제 완료!")

    # --- [탭 2] 기본 학습 ---
    with tab_study:
        current_word = st.session_state.word_list[st.session_state.current_idx]
        mean = st.session_state.words[current_word]
        note = st.session_state.notes.get(current_word, "")
        is_w2m = (st.session_state.direction == "W2M")
        
        if not st.session_state.show_meaning:
            front_text, front_color = (current_word, "#2980B9") if is_w2m else (mean, "#2980B9")
        else:
            front_text, front_color = (mean, "#D35400") if is_w2m else (current_word, "#D35400")

        st.markdown(f"""
        <div style="background-color: #f0f2f6; border-radius: 15px; padding: 40px; text-align: center; border: 3px solid {front_color};">
            <h1 style="color: {front_color}; font-size: 2.5rem; margin: 0;">{front_text}</h1>
        </div><br>
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

    # --- [탭 3] 시험 모드 ---
    with tab_test:
        if not st.session_state.test_active:
            st.subheader("🎯 시험 설정")
            test_type = st.selectbox("시험 방식", ["객관식", "스펠링"])
            max_q = len(st.session_state.word_list)
            q_count = st.number_input(f"문제 수 (최대 {max_q}개)", min_value=1, max_value=max_q, value=min(10, max_q))
            
            if st.button("🚀 시험 시작!", type="primary", use_container_width=True):
                st.session_state.test_active = True
                st.session_state.test_type = test_type
                st.session_state.test_q_max = q_count
                st.session_state.test_q_count = 0
                st.session_state.test_score = 0
                pool = list(st.session_state.word_list)
                random.shuffle(pool)
                st.session_state.test_queue = pool[:q_count]
                prepare_question()
                st.rerun()
        else:
            progress = (st.session_state.test_q_count) / st.session_state.test_q_max
            st.progress(progress)
            st.caption(f"문제: {st.session_state.test_q_count + 1} / {st.session_state.test_q_max} (현재 점수: {st.session_state.test_score})")
            current_w = st.session_state.test_queue[st.session_state.test_q_count]
            
            if st.session_state.test_type == "객관식":
                st.markdown(f"<h2 style='text-align: center; color: #2C3E50;'>{current_w}</h2>", unsafe_allow_html=True)
                st.write("")
                if not st.session_state.test_answered:
                    for opt in st.session_state.test_options:
                        if st.button(opt, use_container_width=True):
                            submit_mcq(opt)
                            st.rerun()
            elif st.session_state.test_type == "스펠링":
                mean = st.session_state.words[current_w]
                st.markdown(f"<h2 style='text-align: center; color: #2C3E50;'>{mean}</h2>", unsafe_allow_html=True)
                st.write("")
                if not st.session_state.test_answered:
                    with st.form(key=f"spell_form_{st.session_state.test_q_count}"):
                        user_spell = st.text_input("위 뜻에 맞는 영어 단어를 입력하세요:")
                        if st.form_submit_button("정답 확인", use_container_width=True):
                            submit_spell(user_spell)
                            st.rerun()
            
            if st.session_state.test_answered:
                if "⭕" in st.session_state.test_msg:
                    st.success(st.session_state.test_msg)
                else:
                    st.error(st.session_state.test_msg)
                
                st.audio(get_audio_player(current_w), format="audio/mp3", autoplay=True)
                
                if st.session_state.test_q_count < st.session_state.test_q_max - 1:
                    if st.button("다음 문제 ➡️", type="primary", use_container_width=True):
                        st.session_state.test_q_count += 1
                        prepare_question()
                        st.rerun()
                else:
                    st.info(f"🎉 시험 종료! 최종 점수: {st.session_state.test_score} / {st.session_state.test_q_max}")
                    # 🎯 시험 종료 시 자동으로 통계를 구글 시트에 업데이트!
                    if st.button("시험 끝내고 결과 저장하기 💾", use_container_width=True):
                        with st.spinner("통계 결과를 구글 시트에 저장하는 중..."):
                            google_db.save_stats(st.session_state.current_sheet, st.session_state.stats)
                        st.session_state.test_active = False
                        st.rerun()

    # --- [탭 4] 📊 현황판 ---
    with tab_stats:
        st.subheader("📊 나의 학습 현황")
        st.write("시험에서 맞추거나 틀린 횟수가 기록됩니다.")
        
        if st.session_state.stats:
            # 많이 틀린 순서대로 정렬하기
            sorted_stats = sorted(st.session_state.stats.items(), key=lambda x: x[1]['wrong'], reverse=True)
            
            for w, data in sorted_stats:
                correct = data.get('correct', 0)
                wrong = data.get('wrong', 0)
                
                # 틀린 횟수가 1번이라도 있으면 빨간색, 아니면 파란색
                color = "#E74C3C" if wrong > 0 else "#3498DB"
                
                with st.container(border=True):
                    st.markdown(f"**{w}** : {st.session_state.words.get(w, '')}")
                    st.markdown(f"<span style='color: {color};'>⭕ 맞춤: {correct}회 | ❌ 틀림: {wrong}회</span>", unsafe_allow_html=True)
        else:
            st.info("아직 누적된 통계가 없습니다. 시험 모드를 플레이해보세요!")
