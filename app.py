import streamlit as st
from datetime import datetime, timedelta
import random
import json
import os
import requests
import urllib.parse
import pandas as pd

DATA_FILE = "ubt_system_data.json"

def load_data():
    default_data = {
        "users": {
            "director": {"password": "123", "role": "Director", "direction": "Барлығы", "limit": None, "blocked": False},
            "teacher1": {"password": "123", "role": "Teacher", "direction": "Барлығы", "limit": None, "blocked": False},
            "student1": {"password": "123", "role": "Student", "direction": "Математика - Физика", "limit": None, "blocked": False},
            "parent1": {"password": "123", "role": "Parent", "direction": "Барлығы", "limit": None, "blocked": False}
        },
        "questions": [],
        "duel_questions": [], 
        "login_logs": [],
        "results": [],
        "duel_results": [],
        "feedback": [],
        "friends": {},
        "notifications": {},
        "duels": [],
        "badges": {}, 
        "chat_messages": [], 
        "bans": {}, 
        "applications": [], 
        "appeals": [], 
        "settings": {
            "timer_enabled": False,
            "timer_duration": 20,
            "duel_timer": 3, 
            "whatsapp_phone": "",
            "allow_export": False
        }
    }
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                loaded = json.load(f)
                for key in default_data:
                    if key not in loaded:
                        loaded[key] = default_data[key]
                for u in loaded["users"]:
                    if "direction" not in loaded["users"][u]:
                        loaded["users"][u]["direction"] = "Математика - Физика"
                for key_sub in ["badges", "chat_messages", "bans", "duel_questions", "duel_results", "notifications", "applications", "appeals", "duels"]:
                    if key_sub not in loaded:
                        loaded[key_sub] = {} if key_sub in ["badges", "bans", "notifications"] else []
                if "duel_timer" not in loaded["settings"]:
                    loaded["settings"]["duel_timer"] = 3
                return loaded
            except Exception:
                return default_data
    return default_data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'app_data' not in st.session_state:
    st.session_state.app_data = load_data()

if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = {}

if 'blocked_users' not in st.session_state:
    st.session_state.blocked_users = {}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

if 'test_submitted' not in st.session_state:
    st.session_state.test_submitted = False

if 'current_test_results' not in st.session_state:
    st.session_state.current_test_results = None

if 'active_duel' not in st.session_state:
    st.session_state.active_duel = None

BAD_WORDS = ["ботк", "сұка", "обал", "шайтан", "тексерілмеген_сөз", "қарапайым_боқтық", "ақымақ", "есек", "мұрын", "құрт", "сорлы"] 

def check_bad_words_and_ban(username, text):
    text_lower = text.lower()
    for word in BAD_WORDS:
        if word in text_lower:
            unban_time = datetime.now() + timedelta(days=15)
            st.session_state.app_data["bans"][username] = unban_time.strftime("%Y-%m-%d %H:%M:%S")
            save_data(st.session_state.app_data)
            return True
    return False

def send_whatsapp_alert(phone, message):
    if not phone:
        return
    try:
        encoded_message = urllib.parse.quote(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_message}&apikey=free"
        requests.get(url, timeout=3)
    except Exception:
        pass

st.set_page_config(page_title="T.A.S UBT.kz - Cosmic Secure Platform", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #070913 0%, #110d24 50%, #1c1033 100%);
        color: #e2e8f0;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #d8b4fe !important;
        font-weight: 700;
        text-shadow: 0 0 15px rgba(216, 180, 254, 0.2);
    }

    p, label, span, .stMarkdown {
        color: #cbd5e1 !important;
    }

    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, .stTextArea textarea {
        background-color: rgba(30, 27, 75, 0.6) !important;
        color: #f3e8ff !important;
        border: 1px solid #7c3aed !important;
        border-radius: 10px !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #c084fc !important;
        box-shadow: 0 0 10px rgba(192, 132, 252, 0.4);
    }

    .stButton button {
        background: linear-gradient(90deg, #7c3aed 0%, #a855f7 100%) !important;
        color: #ffffff !important;
        font-weight: 600;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 1rem;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4);
        transition: all 0.3s ease;
    }

    .stButton button:hover {
        background: linear-gradient(90deg, #6d28d9 0%, #9333ea 100%) !important;
        box-shadow: 0 6px 20px rgba(168, 85, 247, 0.6);
        transform: translateY(-2px);
    }

    section[data-testid="stSidebar"] {
        background-color: #0b0c16;
        border-right: 1px solid rgba(124, 58, 237, 0.2);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(30, 27, 75, 0.4);
        border-radius: 8px;
        color: #c084fc;
        border: 1px solid rgba(124, 58, 237, 0.2);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #7c3aed 0%, #a855f7 100%) !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.title("T.A.S UBT.kz")
    st.markdown("Жүйеге кіру үшін логин мен пароліңізді жазыңыз:")
    
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Кіру"):
        now = datetime.now()
        users_db = st.session_state.app_data["users"]
        
        if username in users_db and users_db[username].get("blocked", False):
            st.error("⛔ Бұл аккаунт директор тарапынан бұғатталған!")
            st.stop()
        
        if username in st.session_state.blocked_users:
            unblock_time = st.session_state.blocked_users[username]
            if now < unblock_time:
                remaining = int((unblock_time - now).total_seconds() / 60)
                st.error(f"Бұл аккаунт уақытша бұғатталған. {remaining} минуттан кейін көріңіз.")
                st.stop()
            else:
                del st.session_state.blocked_users[username]
                st.session_state.login_attempts[username] = 0

        if username in users_db and users_db[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.current_user = username
            st.session_state.login_attempts[username] = 0
            st.session_state.test_submitted = False
            st.session_state.current_test_results = None
            st.session_state.active_duel = None
            
            role = users_db[username]["role"]
            time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            
            st.session_state.app_data["login_logs"].append({
                "user": username,
                "role": role,
                "time": time_str
            })
            save_data(st.session_state.app_data)
            
            if role == "Director":
                ph = st.session_state.app_data["settings"].get("whatsapp_phone", "")
                if ph:
                    msg = f"Назар аударыңыз: Директор ({username}) жүйеге кірді! Уақыты: {time_str}"
                    send_whatsapp_alert(ph, msg)
            
            st.rerun()
        else:
            if username not in st.session_state.login_attempts:
                st.session_state.login_attempts[username] = 0
            st.session_state.login_attempts[username] += 1
            
            attempts_left = 10 - st.session_state.login_attempts[username]
            
            if st.session_state.login_attempts[username] >= 10:
                st.session_state.blocked_users[username] = now + timedelta(minutes=30)
                st.error("Құпия сөз 10 рет қате енгізілді! Аккаунт 30 минутқа бұғатталды.")
            else:
                st.error(f"Қате логин немесе пароль! Қалған әрекеттер саны: {attempts_left}")

else:
    user = st.session_state.current_user
    users_db = st.session_state.app_data["users"]
    
    if user in users_db and users_db[user].get("blocked", False):
        st.error("Сіздің аккаунт бұғатталған!")
        if st.button("Шығу"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()
        st.stop()

    role = users_db[user]["role"]
    
    st.sidebar.title(f"Қош келдіңіз, {user}!")
    st.sidebar.text(f"Рөлі: {role}")
    
    if st.sidebar.button("Жүйеден шығу"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.test_submitted = False
        st.session_state.current_test_results = None
        st.session_state.active_duel = None
        st.rerun()

    if role == "Director":
        st.title("Директордың басқару панелі (T.A.S UBT.kz)")
        whatsapp_phone_saved = st.session_state.app_data["settings"].get("whatsapp_phone", "")
        
        if not whatsapp_phone_saved:
            st.warning("⚠️ Назар аударыңыз! Жүйені толық пайдалану үшін WhatsApp нөміріңізді енгізіңіз.")
            phone_input = st.text_input("WhatsApp нөмірі (мысалы: 77012345678)", key="initial_whatsapp_input")
            if st.button("WhatsApp нөмірін сақтау"):
                if phone_input:
                    st.session_state.app_data["settings"]["whatsapp_phone"] = phone_input
                    save_data(st.session_state.app_data)
                    st.success("Сақталды!")
                    st.rerun()
            st.stop()

        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs([
            "Қолданушылар", "Мұғалім Лимиттері", "Сұрақтар", "⚔️ Дуэль", "🏆 Атақтар", "💬 Ортақ чат", "💬 Чат & Бан", "📥 Заявалар", "⚖️ Аппеляциялар", "📊 Статистика", "Қолданушы қосу", "Баптаулар"
        ])
        
        with tab1:
            st.subheader("👥 Қолданушыларды басқару")
            for u, data in users_db.items():
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1: st.write(f"**{u}** ({data['role']} - Бағыты: {data.get('direction', 'Жоқ')})")
                with col2: st.write(f"{'🔴 Бұғатталған' if data.get('blocked') else '🟢 Белсенді'}")
                with col3:
                    if u != "director":
                        if data.get('blocked'):
                            if st.button("Шығару", key=f"unbl_{u}"):
                                users_db[u]["blocked"] = False
                                save_data(st.session_state.app_data)
                                st.rerun()
                        else:
                            if st.button("Бұғаттау", key=f"bl_{u}"):
                                users_db[u]["blocked"] = True
                                save_data(st.session_state.app_data)
                                st.rerun()

        with tab2:
            st.subheader("⚙️ Мұғалім лимиттері")
            t_list = [u for u, d in users_db.items() if d["role"] == "Teacher"]
            if t_list:
                t_name = st.selectbox("Мұғалім", t_list)
                if st.button("1 Айлық лимит беру"):
                    users_db[t_name]["limit"] = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M')
                    save_data(st.session_state.app_data)
                    st.success("Берілді!")

        with tab3:
            st.subheader("📚 Жалпы тест сұрақтарын басқару")
            q_sub = st.selectbox("Пән", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика", "Биология", "Химия", "Ағылшын тілі", "Дүние жүзі тарихы", "География"])
            q_text = st.text_area("Сұрақ", key="dir_q_text")
            opt_a = st.text_input("A", key="dir_opt_a")
            opt_b = st.text_input("B", key="dir_opt_b")
            opt_c = st.text_input("C", key="dir_opt_c")
            opt_d = st.text_input("D", key="dir_opt_d")
            c_a = st.checkbox("A дұрыс", key="dir_c_a")
            c_b = st.checkbox("B дұрыс", key="dir_c_b")
            c_c = st.checkbox("C дұрыс", key="dir_c_c")
            c_d = st.checkbox("D дұрыс", key="dir_c_d")
            
            if st.button("Қосу", key="dir_add_q_btn"):
                corrects = []
                if c_a: corrects.append("A")
                if c_b: corrects.append("B")
                if c_c: corrects.append("C")
                if c_d: corrects.append("D")
                qs = st.session_state.app_data["questions"]
                new_id = max([q["id"] for q in qs], default=0) + 1
                qs.append({"id": new_id, "subject": q_sub, "text": q_text, "options": {"A": opt_a, "B": opt_b, "C": opt_c, "D": opt_d}, "correct": corrects})
                save_data(st.session_state.app_data)
                st.success("Сәтті қосылды!")

        with tab4:
            st.subheader("⚔️ Дуэль сұрақтары мен уақытын басқару")
            new_duel_timer = st.number_input("Дуэль уақыты (минут)", min_value=1, max_value=60, value=st.session_state.app_data["settings"].get("duel_timer", 3), key="duel_timer_input_field")
            if st.button("Дуэль уақытын сақтау", key="save_duel_timer_btn"):
                st.session_state.app_data["settings"]["duel_timer"] = new_duel_timer
                save_data(st.session_state.app_data)
                st.success(f"Дуэль уақыты {new_duel_timer} минут етіп сақталды!")
            
            st.divider()
            st.subheader("Дуэль сұрағын қосу")
            dq_text = st.text_area("Дуэль сұрағының мәтіні", key="duel_q_text_field")
            dq_a = st.text_input("A нұсқасы", key="dq_a")
            dq_b = st.text_input("B нұсқасы", key="dq_b")
            dq_c = st.text_input("C нұсқасы", key="dq_c")
            dq_d = st.text_input("D нұсқасы", key="dq_d")
            dc_a = st.checkbox("A дұрыс", key="dc_a")
            dc_b = st.checkbox("B дұрыс", key="dc_b")
            dc_c = st.checkbox("C дұрыс", key="dc_c")
            dc_d = st.checkbox("D дұрыс", key="dc_d")
            
            if st.button("Дуэль сұрағын қосу", key="add_duel_q_btn"):
                corrects = []
                if dc_a: corrects.append("A")
                if dc_b: corrects.append("B")
                if dc_c: corrects.append("C")
                if dc_d: corrects.append("D")
                
                d_qs = st.session_state.app_data["duel_questions"]
                new_dq_id = max([q["id"] for q in d_qs], default=0) + 1
                d_qs.append({"id": new_dq_id, "text": dq_text, "options": {"A": dq_a, "B": dq_b, "C": dq_c, "D": dq_d}, "correct": corrects})
                save_data(st.session_state.app_data)
                st.success("Дуэль сұрағы сәтті қосылды!")
                st.rerun()

        with tab5:
            st.subheader("🏆 Оқушыларға атақ (Badge) беру")
            students_list = [u for u, d in users_db.items() if d["role"] == "Student"]
            if students_list:
                sel_student = st.selectbox("Оқушыны таңдаңыз", students_list)
                current_badge = st.session_state.app_data["badges"].get(sel_student, "")
                st.write(f"Қазіргі атағы: **{current_badge if current_badge else 'Жоқ'}**")
                
                badge_input = st.text_input("Жаңа атақ немесе марапат атауы:")
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("Атақты беру/сақтау"):
                        st.session_state.app_data["badges"][sel_student] = badge_input
                        save_data(st.session_state.app_data)
                        st.success(f"{sel_student} оқушысына атақ берілді!")
                        st.rerun()
                with col_b2:
                    if st.button("Атақты алып тастау"):
                        if sel_student in st.session_state.app_data["badges"]:
                            del st.session_state.app_data["badges"][sel_student]
                            save_data(st.session_state.app_data)
                            st.warning("Атақ алынып тасталды!")
                            st.rerun()

        with tab6:
            st.subheader("💬 Ортақ чат (Директор ретінде жазу)")
            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}** ({msg['time']}): {msg['text']}")
                
            dir_msg = st.text_input("Чатқа хабарлама жазу:", key="dir_chat_input")
            if st.button("Директор хабарламасын жіберу"):
                dir_msg_str = str(dir_msg) if dir_msg is not None else ""
                if dir_msg_str and dir_msg_str.strip():
                    chat_messages.append({
                        "user": f"{user} (Директор)",
                        "text": dir_msg_str,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    save_data(st.session_state.app_data)
                    st.rerun()

        with tab7:
            st.subheader("💬 Ортақ чат бан жүйесі")
            bans_db = st.session_state.app_data["bans"]
            now_dt = datetime.now()
            
            active_bans = {}
            for u_ban, b_time_str in bans_db.items():
                b_dt = datetime.strptime(b_time_str, "%Y-%m-%d %H:%M:%S")
                if now_dt < b_dt:
                    active_bans[u_ban] = b_dt
                
            if active_bans:
                for b_user, b_expire in active_bans.items():
                    col_u1, col_u2 = st.columns([3, 1])
                    with col_u1:
                        st.write(f"🔴 **{b_user}** — Бан аяқталуы: {b_expire.strftime('%Y-%m-%d %H:%M')}")
                    with col_u2:
                        if st.button("Unban", key=f"unban_{b_user}"):
                            del st.session_state.app_data["bans"][b_user]
                            save_data(st.session_state.app_data)
                            st.success("Бан алынды!")
                            st.rerun()
            else:
                st.info("Қазір белсенді бан жоқ.")

        with tab8:
            st.subheader("📥 Оқушылардан түскен заявалар")
            applications = st.session_state.app_data.get("applications", [])
            if applications:
                for idx, app in enumerate(reversed(applications)):
                    st.write(f"👤 **Оқушы:** {app['student']} | 🕒 **Уақыты:** {app['time']}")
                    st.markdown(f"> **Мәтіні:** {app['text']}")
                    if st.button("Өшіру", key=f"del_app_{idx}"):
                        applications.remove(app)
                        save_data(st.session_state.app_data)
                        st.rerun()
                    st.divider()
            else:
                st.info("Әзірге заявалар жоқ.")

        with tab9:
            st.subheader("⚖️ Тест кезіндегі аппеляциялар")
            appeals = st.session_state.app_data.get("appeals", [])
            if appeals:
                for idx, ap in enumerate(reversed(appeals)):
                    st.write(f"👤 **Оқушы:** {ap['student']} | 📚 **Пән:** {ap['subject']} | 🕒 **Уақыты:** {ap['time']}")
                    st.markdown(f"> **Шағым мәтіні / Сұрақ:** {ap['text']}")
                    if st.button("Өшіру", key=f"del_ap_{idx}"):
                        appeals.remove(ap)
                        save_data(st.session_state.app_data)
                        st.rerun()
                    st.divider()
            else:
                st.info("Әзірге аппеляциялар жоқ.")

        with tab10:
            st.subheader("📊 Барлық оқушылар нәтижелері")
            results = st.session_state.app_data.get("results", [])
            if results:
                df = pd.DataFrame(results)
                st.dataframe(df)
                st.bar_chart(df.set_index("student")[["score"]])
            else:
                st.info("Нәтижелер жоқ.")

        with tab11:
            st.subheader("🔑 Жаңа қолданушы қосу")
            new_u = st.text_input("Жаңа логин")
            new_p = st.text_input("Пароль", type="password")
            new_r = st.selectbox("Рөл", ["Student", "Parent", "Teacher"])
            
            new_dir = "Барлығы"
            if new_r == "Student":
                new_dir = st.selectbox("Оқушының бағыты", ["Математика - Физика", "Биология - Химия", "Ағылшын - Тарих", "География - Математика"])
            
            if st.button("Қолданушы жасау"):
                if new_u and new_u not in users_db:
                    users_db[new_u] = {
                        "password": new_p, 
                        "role": new_r, 
                        "direction": new_dir, 
                        "limit": None, 
                        "blocked": False
                    }
                    save_data(st.session_state.app_data)
                    st.success("Сәтті жасалды!")
                else:
                    st.error("Қате немесе бос емес логин.")

        with tab12:
            st.subheader("⚙️ Баптаулар")
            st.session_state.app_data["settings"]["timer_enabled"] = st.checkbox("Таймер қосу", value=st.session_state.app_data["settings"]["timer_enabled"])
            st.session_state.app_data["settings"]["timer_duration"] = st.number_input("Уақыт (мин)", value=st.session_state.app_data["settings"]["timer_duration"])
            save_data(st.session_state.app_data)
            st.success("Сақталды!")

    elif role == "Teacher":
        st.title("Мұғалім панелі (T.A.S UBT.kz)")
        t_tab1, t_tab2, t_tab3 = st.tabs(["📚 Сұрақ қосу", "💬 Ортақ чат", "⚖️ Аппеляцияларды қарау"])
        
        with t_tab1:
            t_sub = st.selectbox("Пән", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика", "Биология", "Химия", "Ағылшын тілі", "Дүние жүзі тарихы", "География"])
            t_text = st.text_area("Сұрақ мәтіні")
            o_a = st.text_input("A нұсқасы")
            o_b = st.text_input("B нұсқасы")
            o_c = st.text_input("C нұсқасы")
            o_d = st.text_input("D нұсқасы")
            tc_a = st.checkbox("A дұрыс")
            tc_b = st.checkbox("B дұрыс")
            tc_c = st.checkbox("C дұрыс")
            tc_d = st.checkbox("D дұрыс")
            if st.button("Сұрақ қосу"):
                corrects = []
                if tc_a: corrects.append("A")
                if tc_b: corrects.append("B")
                if tc_c: corrects.append("C")
                if tc_d: corrects.append("D")
                qs = st.session_state.app_data["questions"]
                qs.append({"id": len(qs)+1, "subject": t_sub, "text": t_text, "options": {"A": o_a, "B": o_b, "C": o_c, "D": o_d}, "correct": corrects})
                save_data(st.session_state.app_data)
                st.success("Сұрақ қосылды!")

        with t_tab2:
            st.subheader("💬 Ортақ чат (Мұғалім ретінде жазу)")
            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}** ({msg['time']}): {msg['text']}")
                
            t_msg = st.text_input("Чатқа хабарлама жазу:", key="teacher_chat_input")
            if st.button("Мұғалім хабарламасын жіберу"):
                t_msg_str = str(t_msg) if t_msg is not None else ""
                if t_msg_str and t_msg_str.strip():
                    chat_messages.append({
                        "user": f"{user} (Мұғалім)",
                        "text": t_msg_str,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    save_data(st.session_state.app_data)
                    st.rerun()

        with t_tab3:
            st.subheader("⚖️ Оқушылардан түскен тест аппеляциялары")
            appeals = st.session_state.app_data.get("appeals", [])
            if appeals:
                for idx, ap in enumerate(reversed(appeals)):
                    st.write(f"👤 **Оқушы:** {ap['student']} | 📚 **Пән:** {ap['subject']} | 🕒 **Уақыты:** {ap['time']}")
                    st.markdown(f"> **Шағым мәтіні:** {ap['text']}")
                    if st.button("Тексердім / Өшіру", key=f"t_del_ap_{idx}"):
                        appeals.remove(ap)
                        save_data(st.session_state.app_data)
                        st.rerun()
                    st.divider()
            else:
                st.info("Әзірге аппеляциялар жоқ.")

    elif role == "Parent":
        st.title(f"Ата-ана кабинеті: {user} (T.A.S UBT.kz)")
        tab_p1, tab_p2 = st.tabs(["📊 Балалардың нәтижелері", "💬 Жалпы чат"])
        
        with tab_p1:
            results = st.session_state.app_data.get("results", [])
            if results:
                for r in reversed(results):
                    st.write(f"👤 Оқушы: **{r['student']}** | Пән: **{r['subject']}** | Ұпай: **{r['score']} / {r['total']}**")
            else:
                st.info("Нәтижелер жоқ.")
                
        with tab_p2:
            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}** ({msg['time']}): {msg['text']}")

    elif role == "Student":
        st.title(f"Оқушы кабинеті: {user} (T.A.S UBT.kz)")
        student_direction = users_db[user].get("direction", "Математика - Физика")
        
        my_badge = st.session_state.app_data["badges"].get(user, "")
        if my_badge:
            st.success(f"⭐ Сіздің жеке атағыңыз: **{my_badge}**")
            
        tab_s1, tab_s2, tab_s3, tab_s4, tab_s5, tab_s6, tab_s7, tab_s8 = st.tabs([
            "👤 Профиль", "🏆 Рейтинг", "⚔️ Тест & Аппеляция", "💬 Ортақ чат", "📝 Заява", "⚖️ Менің аппеляцияларым", "📬 Хабарландырулар", "⚔️ Дуэль ойыны"
        ])
        
        with tab_s1:
            st.subheader("👤 Жеке профиль")
            results = st.session_state.app_data.get("results", [])
            my_results = [r for r in results if r['student'] == user]
            st.write(f"**Логин:** {user} | **Бағыт:** {student_direction}")
            if my_results:
                for mr in my_results:
                    st.write(f"- Пән: **{mr['subject']}** | Ұпай: **{mr['score']} / {mr['total']}**")
            else:
                st.info("Тест тапсырған жоқсыз.")

        with tab_s2:
            st.subheader("🏆 Жалпы рейтинг")
            results = st.session_state.app_data.get("results", [])
            student_stats = {}
            for r in results:
                s = r['student']
                if s not in student_stats:
                    student_stats[s] = {"score": 0}
                student_stats[s]["score"] += r['score']
            
            ranking_list = sorted([{"student": s, "score": d["score"]} for s, d in student_stats.items()], key=lambda x: x['score'], reverse=True)
            for idx, item in enumerate(ranking_list):
                st.write(f"**{idx+1}-орын:** {item['student']} — Ұпай: {item['score']}")

        with tab_s3:
            st.subheader("🎯 Тест тапсыру және аппеляция жіберу")
            if not st.session_state.test_submitted:
                subjects = ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы"]
                map_dir = {
                    "Математика - Физика": ["Математика", "Физика"],
                    "Биология - Химия": ["Биология", "Химия"],
                    "Ағылшын - Тарих": ["Ағылшын тілі", "Дүние жүзі тарихы"],
                    "География - Математика": ["География", "Математика"]
                }
                all_subs = subjects + map_dir.get(student_direction, [])
                sel_sub = st.selectbox("Пәнді таңдаңыз", ["Таңдаңыз..."] + all_subs)
                
                if sel_sub != "Таңдаңыз...":
                    qs = [q for q in st.session_state.app_data["questions"] if q["subject"] == sel_sub]
                    if qs:
                        answers = {}
                        for idx, q in enumerate(qs):
                            st.write(f"**Сұрақ {idx+1}:** {q['text']}")
                            for k, v in q['options'].items():
                                st.write(f"{k}) {v}")
                            ans = st.multiselect("Жауап", ["A", "B", "C", "D"], key=f"q_{q['id']}")
                            answers[q['id']] = ans
                            st.divider()
                        
                        if st.button("Тестті аяқтау"):
                            score = 0
                            for q in qs:
                                if set(answers.get(q['id'], [])) == set(q['correct']):
                                    score += 1
                            st.session_state.app_data["results"].append({
                                "student": user, "subject": sel_sub, "score": score, "total": len(qs), "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            save_data(st.session_state.app_data)
                            st.session_state.test_submitted = True
                            st.rerun()
                    else:
                        st.warning("Бұл пән бойынша сұрақтар жоқ.")
            else:
                st.success("Тест аяқталды!")
                
                st.divider()
                st.write("### ⚖️ Сұраққа қатысты аппеляция (шағым) беру:")
                st.info("Егер тесттегі қандай да бір сұрақ қате деп есептесеңіз, аппеляция жібере аласыз.")
                
                ap_subject = st.selectbox("Пәні", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика", "Биология", "Химия", "Ағылшын тілі", "Дүние жүзі тарихы", "География"], key="student_app_sub")
                ap_text = st.text_area("Аппеляция себебі (қай сұрақ, неліктен қате деп ойлайсыз):", key="student_app_txt")
                if st.button("Аппеляцияны жіберу", key="student_send_app_btn"):
                    ap_text_str = str(ap_text) if ap_text is not None else ""
                    if ap_text_str and ap_text_str.strip():
                        if "appeals" not in st.session_state.app_data:
                            st.session_state.app_data["appeals"] = []
                        
                        st.session_state.app_data["appeals"].append({
                            "student": user,
                            "subject": ap_subject,
                            "text": ap_text_str,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        save_data(st.session_state.app_data)
                        st.success("Аппеляция сәтті жіберілді!")
                    else:
                        st.error("Аппеляция мәтіні бос болмауы тиіс.")

        with tab_s4:
            st.subheader("💬 Ортақ чат")
            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}** ({msg['time']}): {msg['text']}")
                
            s_msg = st.text_input("Хабарлама жазу:", key="student_chat_input_field")
            if st.button("Хабарлама жіберу"):
                s_msg_str = str(s_msg) if s_msg is not None else ""
                if s_msg_str and s_msg_str.strip():
                    is_banned = check_bad_words_and_ban(user, s_msg_str)
                    if is_banned:
                        st.error("⛔ Сіздің хабарламаңыздан тыйым салынған сөздер табылды! Жүйе ережесі бойынша чаттағы аккаунтыңыз 15 күнге бұғатталды.")
                    else:
                        chat_messages.append({
                            "user": f"{user} (Оқушы)",
                            "text": s_msg_str,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        save_data(st.session_state.app_data)
                        st.rerun()
                else:
                    st.error("Хабарлама бос болмауы тиіс.")

        with tab_s5:
            st.subheader("📝 Директорға немесе мұғалімге заява (өтініш) жазу")
            app_text = st.text_area("Заяваның мәтіні:", key="student_app_text_field")
            if st.button("Заяваны жіберу"):
                app_text_str = str(app_text) if app_text is not None else ""
                if app_text_str and app_text_str.strip():
                    if "applications" not in st.session_state.app_data:
                        st.session_state.app_data["applications"] = []
                    st.session_state.app_data["applications"].append({
                        "student": user,
                        "text": app_text_str,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    save_data(st.session_state.app_data)
                    st.success("Заява сәтті жіберілді!")
                else:
                    st.error("Заява мәтіні бос болмауы тиіс.")

        with tab_s6:
            st.subheader("⚖️ Мен жіберген аппеляциялар")
            appeals = st.session_state.app_data.get("appeals", [])
            my_appeals = [ap for ap in appeals if ap['student'] == user]
            if my_appeals:
                for ap in reversed(my_appeals):
                    st.write(f"📚 **Пән:** {ap['subject']} | 🕒 **Уақыты:** {ap['time']}")
                    st.markdown(f"> {ap['text']}")
                    st.divider()
            else:
                st.info("Сіз әзірге аппеляция жіберген жоқсыз.")

        with tab_s7:
            st.subheader("📬 Хабарландырулар")
            st.info("Жаңа хабарландырулар жоқ.")

        with tab_s8:
            st.subheader("⚔️ Оқушылар арасындағы дуэль")
            duel_qs = st.session_state.app_data["duel_questions"]
            if duel_qs:
                opponent = st.selectbox("Қарсыласты таңдаңыз", [u for u in users_db if u != user and users_db[u]["role"] == "Student"])
                if opponent:
                    if st.button("Дуэльді бастау"):
                        st.session_state.active_duel = {"opponent": opponent, "score": 0, "q_idx": 0}
                        st.rerun()
                    
                    if st.session_state.active_duel:
                        q_idx = st.session_state.active_duel["q_idx"]
                        if q_idx < len(duel_qs):
                            dq = duel_qs[q_idx]
                            st.write(f"**Дуэль сұрағы {q_idx+1}:** {dq['text']}")
                            d_ans = st.radio("Жауапты таңдаңыз:", ["A", "B", "C", "D"], key=f"duel_q_{q_idx}")
                            if st.button("Жауапты жіберу"):
                                if d_ans in dq['correct']:
                                    st.session_state.active_duel["score"] += 1
                                    st.success("Дұрыс!")
                                else:
                                    st.error("Қате!")
                                st.session_state.active_duel["q_idx"] += 1
                                st.rerun()
                        else:
                            final_score = st.session_state.active_duel["score"]
                            st.session_state.app_data["duel_results"].append({
                                "student": user,
                                "opponent": st.session_state.active_duel["opponent"],
                                "score": final_score,
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            save_data(st.session_state.app_data)
                            st.balloons()
                            st.success(f"Дуэль аяқталды! Сіздің жинаған ұпайыңыз: {final_score}")
                            if st.button("Дуэльді жабу"):
                                st.session_state.active_duel = None
                                st.rerun()
            else:
                st.info("Әзірге дуэль сұрақтары қосылмаған. Директордан сұрақ қосуын өтініңіз.")
