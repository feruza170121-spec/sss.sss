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
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
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

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

if 'test_submitted_sub' not in st.session_state:
    st.session_state.test_submitted_sub = None

BAD_WORDS = ["ботк", "сұка", "обал", "шайтан", "ақымақ", "есек", "сорлы"] 

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
        background: linear-gradient(90deg, #7c3aed 0%, #a855f7 100%) !important; color: #ffffff !important; font-weight: 600; border-radius: 10px; border: none; padding: 0.5rem 1rem; box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4);
    }
    section[data-testid="stSidebar"] { background-color: #0b0c16; border-right: 1px solid rgba(124, 58, 237, 0.2); }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.title("T.A.S UBT.kz")
    st.markdown("Жүйеге кіру үшін логин мен пароліңізді жазыңыз:")
    
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Кіру"):
        users_db = st.session_state.app_data["users"]
        hashed_pwd = hash_password(password)
        
        if username in users_db and users_db[username]["password"] == hashed_pwd:
            if users_db[username].get("blocked", False):
                st.error("⛔ Бұл аккаунт бұғатталған!")
            else:
                st.session_state.logged_in = True
                st.session_state.current_user = username
                st.rerun()
        else:
            st.error("Қате логин немесе пароль!")

else:
    user = st.session_state.current_user
    users_db = st.session_state.app_data["users"]
    role = users_db[user]["role"]
    
    st.sidebar.title(f"Қош келдіңіз, {user}!")
    st.sidebar.text(f"Рөлі: {role}")
    
    if st.sidebar.button("Жүйеден шығу"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
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
                with col1: st.write(f"**{u}** ({data['role']})")
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
            q_sub = st.selectbox("Пән", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика", "Биология", "Химия", "Ағылшын тілі"], key="dir_q_sub")
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
            st.subheader("⚔️ Дуэль уақытын басқару")
            new_duel_timer = st.number_input("Дуэль уақыты (минут)", min_value=1, max_value=60, value=st.session_state.app_data["settings"].get("duel_timer", 3))
            if st.button("Сақтау"):
                st.session_state.app_data["settings"]["duel_timer"] = new_duel_timer
                save_data(st.session_state.app_data)
                st.success("Сақталды!")

        with tab5:
            st.subheader("🏆 Оқушыларға атақ беру")
            students_list = [u for u, d in users_db.items() if d["role"] == "Student"]
            if students_list:
                sel_student = st.selectbox("Оқушы", students_list, key="dir_badge_sel")
                badge_input = st.text_input("Атақ", key="dir_badge_inp")
                if st.button("Беру", key="dir_badge_btn"):
                    st.session_state.app_data["badges"][sel_student] = badge_input
                    save_data(st.session_state.app_data)
                    st.success("Сақталды!")

        with tab6, tab7:
            st.subheader("💬 Ортақ чат & Бандар")
            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}** ({msg['time']}): {msg['text']}")
            dir_msg = st.text_input("Хабарлама:", key="dir_chat_input")
            if st.button("Жіберу", key="dir_chat_btn"):
                if dir_msg.strip():
                    chat_messages.append({"user": f"{user} (Директор)", "text": dir_msg, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    save_data(st.session_state.app_data)
                    st.rerun()

        with tab8:
            st.subheader("📥 Заявалар")
            for app in reversed(st.session_state.app_data.get("applications", [])):
                st.write(f"👤 {app['student']} | 🕒 {app['time']}")
                st.markdown(f"> {app['text']}")
                st.divider()

        with tab9:
            st.subheader("⚖️ Аппеляциялар")
            for ap in reversed(st.session_state.app_data.get("appeals", [])):
                st.write(f"👤 {ap['student']} | 📚 {ap['subject']} | 🕒 {ap['time']}")
                st.markdown(f"> {ap['text']}")
                st.divider()

        with tab10:
            st.subheader("📊 Статистика")
            results = st.session_state.app_data.get("results", [])
            if results:
                st.dataframe(pd.DataFrame(results))

        with tab11:
            st.subheader("🔑 Қолданушы қосу")
            new_u = st.text_input("Логин", key="add_u")
            new_p = st.text_input("Пароль", type="password", key="add_p")
            new_r = st.selectbox("Рөл", ["Student", "Parent", "Teacher"], key="add_r")
            if st.button("Жасау", key="add_btn"):
                if new_u and new_u not in users_db:
                    users_db[new_u] = {"password": hash_password(new_p), "role": new_r, "direction": "Математика - Физика", "child": "student1", "limit": None, "blocked": False}
                    save_data(st.session_state.app_data)
                    st.success("Сәтті жасалды!")

        with tab12:
            st.subheader("Баптаулар")
            st.info("Барлық параметрлер орнында.")

    elif role == "Teacher":
        st.title("Мұғалім панелі")
        t_sub = st.selectbox("Пән", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика"])
        t_text = st.text_area("Сұрақ мәтіні")
        o_a = st.text_input("A")
        o_b = st.text_input("B")
        o_c = st.text_input("C")
        o_d = st.text_input("D")
        if st.button("Қосу"):
            qs = st.session_state.app_data["questions"]
            qs.append({"id": len(qs)+1, "subject": t_sub, "text": t_text, "options": {"A": o_a, "B": o_b, "C": o_c, "D": o_d}, "correct": ["A"]})
            save_data(st.session_state.app_data)
            st.success("Қосылды!")

    elif role == "Parent":
        st.title(f"Ата-ана кабинеті: {user}")
        child_name = users_db[user].get("child", "student1")
        st.subheader(f"Баланың ({child_name}) нәтижелері:")
        results = [r for r in st.session_state.app_data.get("results", []) if r['student'] == child_name]
        for r in results:
            st.write(f"Пән: {r['subject']} | Ұпай: {r['score']} / {r['total']}")

    elif role == "Student":
        st.title(f"Оқушы кабинеті: {user}")
        tab_s1, tab_s2, tab_s3, tab_s4 = st.tabs(["👤 Профиль", "🎯 Тест тапсыру", "💬 Ортақ чат", "⚔️ Дуэль"])
        
        with tab_s1:
            st.write(f"Логин: {user}")
            my_results = [r for r in st.session_state.app_data.get("results", []) if r['student'] == user]
            for mr in my_results:
                st.write(f"Пән: {mr['subject']} - Ұпай: {mr['score']}/{mr['total']}")

        with tab_s2:
            sel_sub = st.selectbox("Пәнді таңдаңыз", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика"])
            qs = [q for q in st.session_state.app_data["questions"] if q["subject"] == sel_sub]
            if qs:
                answers = {}
                for idx, q in enumerate(qs):
                    st.write(f"Сұрақ {idx+1}: {q['text']}")
                    for k, v in q['options'].items():
                        st.write(f"{k}) {v}")
                    answers[q['id']] = st.multiselect("Жауап", ["A", "B", "C", "D"], key=f"q_{q['id']}")
                
                if st.button("Тестті аяқтау"):
                    score = sum(1 for q in qs if set(answers.get(q['id'], [])) == set(q['correct']))
                    st.session_state.app_data["results"].append({
                        "student": user, "subject": sel_sub, "score": score, "total": len(qs), "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    save_data(st.session_state.app_data)
                    st.success(f"Нәтижеңіз: {score}/{len(qs)}")
            else:
                st.info("Бұл пән бойынша сұрақтар әзірге жоқ.")

        with tab_s3:
            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}**: {msg['text']}")
            s_msg = st.text_input("Хабарлама:", key="s_chat")
            if st.button("Жіберу", key="s_chat_btn"):
                if s_msg.strip():
                    if not check_bad_words_and_ban(user, s_msg):
                        chat_messages.append({"user": user, "text": s_msg, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                        save_data(st.session_state.app_data)
                        st.rerun()
                    else:
                        st.error("⚠️ Тыйым салынған сөз үшін банға іліктіңіз!")

        with tab_s4:
            st.subheader("Дуэль ойыны")
            st.info("Дуэль сұрақтары дайындалуда.")
