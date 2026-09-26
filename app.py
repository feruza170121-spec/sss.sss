import streamlit as st
from datetime import datetime, timedelta
import random
import json
import os
import requests
import urllib.parse
import pandas as pd
import hashlib

DATA_FILE = "ubt_system_data.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_data():
    default_data = {
        "users": {
            "director": {"password": hash_password("123"), "role": "Director", "direction": "Барлығы", "child": "", "limit": None, "blocked": False},
            "teacher1": {"password": hash_password("123"), "role": "Teacher", "direction": "Барлығы", "child": "", "limit": None, "blocked": False},
            "student1": {"password": hash_password("123"), "role": "Student", "direction": "Математика - Физика", "child": "", "limit": None, "blocked": False},
            "parent1": {"password": hash_password("123"), "role": "Parent", "direction": "Барлығы", "child": "student1", "limit": None, "blocked": False}
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
                # Ескі файлда парольдер хэштелмеген болса, автоматты түрде түзеу үшін немесе key жетіспесе толықтыру:
                for u in loaded.get("users", {}):
                    if len(loaded["users"][u]["password"]) != 64: # SHA256 хэші 64 символ болады
                        loaded["users"][u]["password"] = hash_password("123")
                
                for key in default_data:
                    if key not in loaded:
                        loaded[key] = default_data[key]
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

if 'test_submitted_sub' not in st.session_state:
    st.session_state.test_submitted_sub = None

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

st.set_page_config(page_title="T.A.S UBT.kz - Secure Platform", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
    .stApp { background: linear-gradient(135deg, #070913 0%, #110d24 50%, #1c1033 100%); color: #e2e8f0; }
    h1, h2, h3, h4, h5, h6 { color: #d8b4fe !important; font-weight: 700; text-shadow: 0 0 15px rgba(216, 180, 254, 0.2); }
    p, label, span, .stMarkdown { color: #cbd5e1 !important; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, .stTextArea textarea {
        background-color: rgba(30, 27, 75, 0.6) !important; color: #f3e8ff !important; border: 1px solid #7c3aed !important; border-radius: 10px !important;
    }
    .stButton button {
        background: linear-gradient(90deg, #7c3aed 0%, #a855f7 100%) !important; color: #ffffff !important; font-weight: 600; border-radius: 10px; border: none; padding: 0.5rem 1rem; box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4); transition: all 0.3s ease;
    }
    .stButton button:hover { background: linear-gradient(90deg, #6d28d9 0%, #9333ea 100%) !important; box-shadow: 0 6px 20px rgba(168, 85, 247, 0.6); transform: translateY(-2px); }
    section[data-testid="stSidebar"] { background-color: #0b0c16; border-right: 1px solid rgba(124, 58, 237, 0.2); }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(30, 27, 75, 0.4); border-radius: 8px; color: #c084fc; border: 1px solid rgba(124, 58, 237, 0.2); }
    .stTabs [aria-selected="true"] { background: linear-gradient(90deg, #7c3aed 0%, #a855f7 100%) !important; color: white !important; }
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

        hashed_pwd = hash_password(password)
        if username in users_db and users_db[username]["password"] == hashed_pwd:
            st.session_state.logged_in = True
            st.session_state.current_user = username
            st.session_state.login_attempts[username] = 0
            st.session_state.test_submitted_sub = None
            st.session_state.active_duel = None
            
            role = users_db[username]["role"]
            time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            
            st.session_state.app_data["login_logs"].append({"user": username, "role": role, "time": time_str})
            save_data(st.session_state.app_data)
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
        st.session_state.test_submitted_sub = None
        st.session_state.active_duel = None
        st.rerun()

    if role == "Director":
        st.title("Директордың басқару панелі (T.A.S UBT.kz)")
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
                t_name = st.selectbox("Мұғалім", t_list, key="dir_t_limit_sel")
                if st.button("1 Айлық лимит беру", key="dir_t_limit_btn"):
                    users_db[t_name]["limit"] = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M')
                    save_data(st.session_state.app_data)
                    st.success("Берілді!")

        with tab3:
            st.subheader("📚 Жалпы тест сұрақтарын басқару")
            q_sub = st.selectbox("Пән", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика", "Биология", "Химия", "Ағылшын тілі", "Дүние жүзі тарихы", "География"], key="dir_q_sub")
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

        with tab5:
            st.subheader("🏆 Оқушыларға атақ (Badge) беру")
            students_list = [u for u, d in users_db.items() if d["role"] == "Student"]
            if students_list:
                sel_student = st.selectbox("Оқушыны таңдаңыз", students_list, key="dir_badge_sel")
                badge_input = st.text_input("Жаңа атақ:", key="dir_badge_inp")
                if st.button("Атақты беру", key="dir_badge_btn"):
                    st.session_state.app_data["badges"][sel_student] = badge_input
                    save_data(st.session_state.app_data)
                    st.success("Сақталды!")

        with tab6:
            st.subheader("💬 Ортақ чат (Директор)")
            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}** ({msg['time']}): {msg['text']}")
            dir_msg = st.text_input("Хабарлама:", key="dir_chat_input")
            if st.button("Жіберу", key="dir_chat_btn"):
                if dir_msg and dir_msg.strip():
                    if not check_bad_words_and_ban(user, dir_msg):
                        chat_messages.append({"user": f"{user} (Директор)", "text": dir_msg, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                        save_data(st.session_state.app_data)
                        st.rerun()

        with tab7:
            st.subheader("💬 Бан жүйесі")
            bans_db = st.session_state.app_data["bans"]
            now_dt = datetime.now()
            for b_user, b_time_str in list(bans_db.items()):
                b_dt = datetime.strptime(b_time_str, "%Y-%m-%d %H:%M:%S")
                if now_dt < b_dt:
                    c1, c2 = st.columns([3, 1])
                    with c1: st.write(f"🔴 **{b_user}** — {b_dt.strftime('%Y-%m-%d %H:%M')}")
                    with c2:
                        if st.button("Unban", key=f"unban_{b_user}"):
                            del st.session_state.app_data["bans"][b_user]
                            save_data(st.session_state.app_data)
                            st.rerun()

        with tab8:
            st.subheader("📥 Заявалар")
            for idx, app in enumerate(reversed(st.session_state.app_data.get("applications", []))):
                st.write(f"👤 {app['student']} | 🕒 {app['time']}")
                st.markdown(f"> {app['text']}")
                st.divider()

        with tab9:
            st.subheader("⚖️ Аппеляциялар")
            for idx, ap in enumerate(reversed(st.session_state.app_data.get("appeals", []))):
                st.write(f"👤 {ap['student']} | 📚 {ap['subject']} | 🕒 {ap['time']}")
                st.markdown(f"> {ap['text']}")
                st.divider()

        with tab10:
            st.subheader("📊 Рейтинг")
            results = st.session_state.app_data.get("results", [])
            if results:
                df = pd.DataFrame(sorted(results, key=lambda x: x['score'], reverse=True))
                st.dataframe(df)

        with tab11:
            st.subheader("🔑 Қолданушы қосу")
            new_u = st.text_input("Логин", key="add_u")
            new_p = st.text_input("Пароль", type="password", key="add_p")
            new_r = st.selectbox("Рөл", ["Student", "Parent", "Teacher"], key="add_r")
            new_dir = "Барлығы"
            new_child = "student1"
            if new_r == "Student":
                new_dir = st.selectbox("Бағыт", ["Математика - Физика", "Биология - Химия", "Ағылшын - Тарих", "География - Математика"], key="add_dir")
            elif new_r == "Parent":
                new_child = st.text_input("Баласының логині", value="student1", key="add_child")
            
            if st.button("Жасау", key="add_btn"):
                if new_u and new_u not in users_db:
                    users_db[new_u] = {"password": hash_password(new_p), "role": new_r, "direction": new_dir, "child": new_child, "limit": None, "blocked": False}
                    save_data(st.session_state.app_data)
                    st.success("Сәтті жасалды!")

        with tab12:
            st.subheader("⚙️ Баптаулар")
            st.session_state.app_data["settings"]["timer_enabled"] = st.checkbox("Таймер", value=st.session_state.app_data["settings"]["timer_enabled"])
            save_data(st.session_state.app_data)

    elif role == "Teacher":
        st.title("Мұғалім панелі (T.A.S UBT.kz)")
        t_tab1, t_tab2, t_tab3 = st.tabs(["📚 Сұрақ қосу", "💬 Ортақ чат", "⚖️ Аппеляциялар"])
        
        with t_tab1:
            st.subheader("Мұғалімнің жеке кабинеті арқылы сұрақ қосуы")
            t_sub = st.selectbox("Пән", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика", "Биология", "Химия", "Ағылшын тілі", "Дүние жүзі тарихы", "География"], key="t_sub_sel")
            t_text = st.text_area("Сұрақ мәтіні", key="t_q_text")
            o_a = st.text_input("A", key="t_oa")
            o_b = st.text_input("B", key="t_ob")
            o_c = st.text_input("C", key="t_oc")
            o_d = st.text_input("D", key="t_od")
            tc_a = st.checkbox("A дұрыс", key="t_ca")
            tc_b = st.checkbox("B дұрыс", key="t_cb")
            tc_c = st.checkbox("C дұрыс", key="t_cc")
            tc_d = st.checkbox("D дұрыс", key="t_cd")
            if st.button("Сұрақ қосу", key="t_add_btn"):
                corrects = []
                if tc_a: corrects.append("A")
                if tc_b: corrects.append("B")
                if tc_c: corrects.append("C")
                if tc_d: corrects.append("D")
                qs = st.session_state.app_data["questions"]
                new_id = max([q["id"] for q in qs], default=0) + 1
                qs.append({"id": new_id, "subject": t_sub, "text": t_text, "options": {"A": o_a, "B": o_b, "C": o_c, "D": o_d}, "correct": corrects})
                save_data(st.session_state.app_data)
                st.success("Сұрақ қосылды!")

        with t_tab2:
            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}** ({msg['time']}): {msg['text']}")
            t_msg = st.text_input("Хабарлама:", key="t_chat_input")
            if st.button("Жіберу", key="t_chat_btn"):
                if t_msg and t_msg.strip():
                    if not check_bad_words_and_ban(user, t_msg):
                        chat_messages.append({"user": f"{user} (Мұғалім)", "text": t_msg, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                        save_data(st.session_state.app_data)
                        st.rerun()

        with t_tab3:
            for idx, ap in enumerate(reversed(st.session_state.app_data.get("appeals", []))):
                st.write(f"👤 {ap['student']} | 📚 {ap['subject']} | 🕒 {ap['time']}")
                st.markdown(f"> {ap['text']}")
                st.divider()

    elif role == "Parent":
        st.title(f"Ата-ана кабинеті: {user} (T.A.S UBT.kz)")
        child_name = users_db[user].get("child", "student1")
        tab_p1, tab_p2 = st.tabs([f"📊 Баланың ({child_name}) нәтижелері", "💬 Жалпы чат"])
        
        with tab_p1:
            results = [r for r in st.session_state.app_data.get("results", []) if r['student'] == child_name]
            if results:
                for r in sorted(results, key=lambda x: x['score'], reverse=True):
                    st.write(f"📚 Пән: **{r['subject']}** | Ұпай: **{r['score']} / {r['total']}** | Күні: {r['date']}")
            else:
                st.info(f"{child_name} әзірге тест тапсырмаған.")
                
        with tab_p2:
            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}** ({msg['time']}): {msg['text']}")
            p_msg = st.text_input("Хабарлама:", key="p_chat_input")
            if st.button("Жіберу", key="p_chat_btn"):
                if p_msg and p_msg.strip():
                    if not check_bad_words_and_ban(user, p_msg):
                        chat_messages.append({"user": f"{user} (Ата-ана)", "text": p_msg, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                        save_data(st.session_state.app_data)
                        st.rerun()

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
            my_results = [r for r in st.session_state.app_data.get("results", []) if r['student'] == user]
            st.write(f"**Логин:** {user} | **Бағыт:** {student_direction}")
            for mr in my_results:
                st.write(f"- Пән: **{mr['subject']}** | Ұпай: **{mr['score']} / {mr['total']}**")

        with tab_s2:
            st.subheader("🏆 Жалпы рейтинг")
            results = st.session_state.app_data.get("results", [])
            student_stats = {}
            for r in results:
                s = r['student']
                if s not in student_stats: student_stats[s] = {"score": 0}
                student_stats[s]["score"] += r['score']
            for idx, item in enumerate(sorted([{"student": s, "score": d["score"]} for s, d in student_stats.items()], key=lambda x: x['score'], reverse=True)):
                st.write(f"**{idx+1}-орын:** {item['student']} — Ұпай: {item['score']}")

        with tab_s3:
            st.subheader("🎯 Тест тапсыру")
            subjects = ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы"]
            map_dir = {
                "Математика - Физика": ["Математика", "Физика"],
                "Биология - Химия": ["Биология", "Химия"],
                "Ағылшын - Тарих": ["Ағылшын тілі", "Дүние жүзі тарихы"],
                "География - Математика": ["География", "Математика"]
            }
            all_subs = subjects + map_dir.get(student_direction, ["Математика", "Физика"])
            sel_sub = st.selectbox("Пәнді таңдаңыз", ["Таңдаңыз..."] + all_subs, key="student_test_sub")
            
            if sel_sub != "Таңдаңыз...":
                if st.session_state.test_submitted_sub == sel_sub:
                    st.success(f"Сіз бұл пәннен ({sel_sub}) тест тапсырып қойдыңыз!")
                    if st.button("Басқа пән таңдау немесе қайта тапсыру"):
                        st.session_state.test_submitted_sub = None
                        st.rerun()
                else:
                    qs = [q for q in st.session_state.app_data["questions"] if q["subject"] == sel_sub]
                    if qs:
                        with st.container():
                            answers = {}
                            for idx, q in enumerate(qs):
                                st.markdown(f"### Сұрақ {idx+1}: {q['text']}")
                                for k, v in q['options'].items():
                                    st.write(f"{k}) {v}")
                                ans = st.multiselect("Жауап", ["A", "B", "C", "D"], key=f"q_ans_{q['id']}")
                                answers[q['id']] = ans
                                st.divider()
                            
                            if st.button("Тестті аяқтау", key="finish_test_btn"):
                                score = 0
                                for q in qs:
                                    if set(answers.get(q['id'], [])) == set(q['correct']):
                                        score += 1
                                st.session_state.app_data["results"].append({
                                    "student": user, "subject": sel_sub, "score": score, "total": len(qs), "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                                })
                                save_data(st.session_state.app_data)
                                st.session_state.test_submitted_sub = sel_sub
                                st.rerun()
                    else:
                        st.warning("Бұл пән бойынша сұрақтар жоқ.")

        with tab_s4:
            st.subheader("💬 Ортақ чат")
            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}** ({msg['time']}): {msg['text']}")
                
            s_msg = st.text_input("Хабарлама:", key="student_chat_input")
            if st.button("Жіберу", key="s_send_chat_btn"):
                if s_msg and s_msg.strip():
                    if not check_bad_words_and_ban(user, s_msg):
                        chat_messages.append({"user": user, "text": s_msg, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                        save_data(st.session_state.app_data)
                        st.rerun()
                    else:
                        st.error("⚠️ Тыйым салынған сөз қолданғаныңыз үшін 15 күнге банға іліктіңіз!")

        with tab_s5:
            st.subheader("📝 Заява жазу")
            app_text_input = st.text_area("Өтініш мәтіні:", key="stud_app_inp")
            if st.button("Жіберу", key="stud_app_btn"):
                if app_text_input and app_text_input.strip():
                    st.session_state.app_data["applications"].append({"student": user, "text": app_text_input, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    save_data(st.session_state.app_data)
                    st.success("Жіберілді!")

        with tab_s6:
            st.subheader("⚖️ Менің аппеляцияларым")
            for ma in [a for a in st.session_state.app_data.get("appeals", []) if a['student'] == user]:
                st.write(f"📚 {ma['subject']} | 🕒 {ma['time']}")
                st.markdown(f"> {ma['text']}")
                st.divider()

        with tab_s7:
            st.subheader("📬 Хабарландырулар")
            st.info("Жаңа хабарландырулар жоқ.")

        with tab_s8:
            st.subheader("⚔️ Дуэль ойыны")
            d_questions = st.session_state.app_data.get("duel_questions", [])
            if d_questions:
                duel_q = random.choice(d_questions)
                st.write(f"⚔️ **Дуэль сұрағы:** {duel_q['text']}")
                for dk, dv in duel_q['options'].items():
                    st.write(f"{dk}) {dv}")
                d_ans = st.multiselect("Жауап", ["A", "B", "C", "D"], key="duel_ans")
                if st.button("Тапсыру", key="duel_btn"):
                    if set(d_ans) == set(duel_q['correct']):
                        st.success("🎉 Жеңіс!")
                    else:
                        st.error("❌ Қате!")
            else:
                st.info("Дуэль сұрақтары әзірге жоқ.")
