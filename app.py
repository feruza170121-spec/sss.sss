import streamlit as st
from datetime import datetime

# Қара фон мен жасыл мәтінге арналған CSS стильдері
st.markdown("""
    <style>
    /* Негізгі фонды қара түске өзгерту */
    .stApp {
        background-color: #0e1117;
        color: #00FF66;
    }
    
    /* Барлық мәтіндер мен тақырыптарды жасыл ету */
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #00FF66 !important;
    }
    
    /* Мәтін енгізетін өрістер мен аймақтар */
    .stTextInput input, .stTextArea textarea {
        background-color: #1a1c23 !important;
        color: #00FF66 !important;
        border: 1px solid #00FF66 !important;
    }
    
    /* Кнопкалардың түсі */
    .stButton button {
        background-color: #00FF66 !important;
        color: #0e1117 !important;
        font-weight: bold;
    }
    
    /* Sidebar (Бүйірлік панель) дизайны */
    [data-testid="stSidebar"] {
        background-color: #12161f;
    }
    [data-testid="stSidebar"] * {
        color: #00FF66 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Жүйенің қалған бөлігі (алдыңғы код)
def run_student_tabs(user, save_data, check_bad_words_and_ban):
    tab_s4, tab_s5, tab_s6, tab_s7 = st.tabs(["💬 Ортақ чат", "📝 Заява", "⚖️ Аппеляция", "📬 Хабарландырулар"])
    
    with tab_s4:
        st.subheader("💬 Ортақ чат")
        
        now_dt = datetime.now()
        bans_db = st.session_state.app_data.get("bans", {})
        if user in bans_db:
            b_expire = datetime.strptime(bans_db[user], "%Y-%m-%d %H:%M:%S")
            if now_dt < b_expire:
                st.error(f"⛔ Сіздің чатта жазуыңызға тыйым салынған! Бан уақыты: {b_expire.strftime('%Y-%m-%d %H:%M')}")
            else:
                del st.session_state.app_data["bans"][user]
                save_data(st.session_state.app_data)

        chat_messages = st.session_state.app_data.get("chat_messages", [])
        for msg in chat_messages:
            st.write(f"💬 **{msg['user']}** ({msg['time']}): {msg['text']}")
            
        with st.form("student_chat_form", clear_on_submit=True):
            s_msg = st.text_input("Хабарлама жазу:")
            if st.form_submit_button("Жіберу"):
                if s_msg.strip():
                    if check_bad_words_and_ban(user, s_msg):
                        st.error("⛔ Әдепсіз сөздер үшін чатта 15 күнге бұғатталдыңыз!")
                    else:
                        chat_messages.append({
                            "user": f"{user} (Оқушы)",
                            "text": s_msg,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        save_data(st.session_state.app_data)
                        st.rerun()

    with tab_s5:
        st.subheader("📝 Директорға немесе мұғалімдерге заява жіберу")
        with st.form("application_form", clear_on_submit=True):
            app_text = st.text_area("Заява мәтіні (арыз немесе өтініш):")
            if st.form_submit_button("Заяваны жіберу"):
                if app_text.strip():
                    if "applications" not in st.session_state.app_data:
                        st.session_state.app_data["applications"] = []
                    st.session_state.app_data["applications"].append({
                        "student": user,
                        "text": app_text,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    save_data(st.session_state.app_data)
                    st.success("Заяваңыз сәтті жіберілді!")

    with tab_s6:
        st.subheader("⚖️ Менің жіберген аппеляцияларым")
        appeals = st.session_state.app_data.get("appeals", [])
        my_appeals = [ap for ap in appeals if ap['student'] == user]
        if my_appeals:
            for ap in my_appeals:
                st.write(f"📚 **Пән:** {ap['subject']} | 🕒 **Уақыты:** {ap['time']}")
                st.markdown(f"> **Шағымыңыз:** {ap['text']}")
                st.divider()
        else:
            st.info("Сіз әзірге аппеляция жіберген жоқсыз.")

    with tab_s7:
        st.subheader("📬 Хабарландырулар")
        notifications = st.session_state.app_data.get("notifications", {})
        user_notifs = notifications.get(user, [])
        if user_notifs:
            for n in user_notifs:
                st.info(n)
        else:
            st.info("Жаңа хабарландырулар жоқ.")
