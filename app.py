import streamlit as st
from datetime import datetime

# Бүйірлік панельде дизайн режимін таңдау (Түн және Күн режимі)
st.sidebar.title("🎨 Дизайн баптауы")
theme = st.sidebar.radio("Режимді таңдаңыз:", ["🌙 Түн режимі (Қара фон / Жасыл сөздер)", "☀️ Күн режимі (Ақ фон / Қара сөздер)"])

# Режимге байланысты түстерді анықтау
if theme.startswith("🌙"):
    bg_color = "#0e1117"
    text_color = "#00FF66"
    input_bg = "#1a1c23"
    sidebar_bg = "#12161f"
else:
    bg_color = "#ffffff"
    text_color = "#000000"
    input_bg = "#f0f2f6"
    sidebar_bg = "#f8f9fa"

# Динамикалық CSS стильдері (Сіз жіберген стильдерді режимге сай бейімдедім)
st.markdown(f"""
    <style>
    /* Негізгі фон мен мәтін түсі */
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    
    /* Барлық мәтіндер мен тақырыптар */
    h1, h2, h3, h4, h5, h6, p, span, label, div {{
        color: {text_color} !important;
    }}
    
    /* Мәтін енгізетін өрістер мен аймақтар */
    .stTextInput input, .stTextArea textarea {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
        border: 1px solid {text_color} !important;
    }}
    
    /* Кнопкалардың түсі */
    .stButton button {{
        background-color: {text_color} !important;
        color: {bg_color} !important;
        font-weight: bold;
    }}
    
    /* Sidebar (Бүйірлік панель) дизайны */
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg};
    }}
    [data-testid="stSidebar"] * {{
        color: {text_color} !important;
    }}
    </style>
""", unsafe_allow_html=True)

# Жүйенің сіз жіберген код бөлігі
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
