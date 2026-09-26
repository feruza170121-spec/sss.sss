import streamlit as st
from datetime import datetime, timedelta
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

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

if 'test_submitted' not in st.session_state:
    st.session_state.test_submitted = False

if 'current_test_results' not in st.session_state:
    st.session_state.current_test_results = None

if 'active_duel' not in st.session_state:
    st.session_state.active_duel = None

def send_whatsapp_alert(phone, message):
    if not phone:
        return
    try:
        encoded_message = urllib.parse.quote(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_message}&apikey=free"
        requests.get(url, timeout=3)
    except Exception:
        pass

st.set_page_config(page_title="T.A.S UBT.kz", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
    .stApp { background: linear-gradient(135deg, #070913 0%, #110d24 50%, #1c1033 100%); color: #e2e8f0; }
    h1, h2, h3, h4, h5, h6 { color: #d8b4fe !important; font-weight: 700; }
    p, label, span, .stMarkdown { color: #cbd5e1 !important; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, .stTextArea textarea {
        background-color: rgba(30, 27, 75, 0.6) !important; color: #f3e8ff !important; border: 1px solid #7c3aed !important; border-radius: 10px !important;
    }
    .stButton button {
        background: linear-gradient(90deg, #7c3aed 0%, #a855f7 100%) !important; color: #ffffff !important; font-weight: 600; border-radius: 10px; border: none; padding: 0.5rem 1rem;
    }
    section[data-testid="stSidebar"] { background-color: #0b0c16; border-right: 1px solid rgba(124, 58, 237, 0.2); }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.title("T.A.S UBT.kz - Кіру")
    st.markdown("Жүйеге кіру үшін логин мен парольді енгізіңіз:")
    
    username = st.text_input("Логин", key="login_username")
    password = st.text_input("Пароль", type="password", key="login_password")
    
    if st.button("Кіру"):
        users_db = st.session_state.app_data["users"]
        if username in users_db and users_db[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.current_user = username
            st.session_state.test_submitted = False
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
        st.title("Директордың басқару панелі")
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "Қолданушылар", "Сұрақтар", "Дуэль", "Атақтар", "Ортақ чат", "Заявалар", "Аппеляциялар", "Статистика"
        ])
        
        with tab1:
            st.subheader("👥 Қолданушылар тізімі")
            for u, data in users_db.items():
                st.write(f"- **{u}** ({data['role']} - Бағыты: {data.get('direction', 'Жоқ')})")
                
        with tab2:
            st.subheader("📚 Сұрақ қосу")
            q_sub = st.selectbox("Пән", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика"])
            q_text = st.text_area("Сұрақ мәтіні")
            opt_a = st.text_input("A нұсқасы")
            opt_b = st.text_input("B нұсқасы")
            opt_c = st.text_input("C нұсқасы")
            opt_d = st.text_input("D нұсқасы")
            c_a = st.checkbox("A дұрыс")
            c_b = st.checkbox("B дұрыс")
            c_c = st.checkbox("C дұрыс")
            c_d = st.checkbox("D дұрыс")
            if st.button("Сұрақты сақтау"):
                corrects = []
                if c_a: corrects.append("A")
                if c_b: corrects.append("B")
                if c_c: corrects.append("C")
                if c_d: corrects.append("D")
                qs = st.session_state.app_data["questions"]
                qs.append({"id": len(qs)+1, "subject": q_sub, "text": q_text, "options": {"A": opt_a, "B": opt_b, "C": opt_c, "D": opt_d}, "correct": corrects})
                save_data(st.session_state.app_data)
                st.success("Сәтті қосылды!")

        with tab3:
            st.subheader("⚔️ Дуэль сұрақтары")
            dq_text = st.text_area("Дуэль сұрағы")
            dq_a = st.text_input("A", key="dq_a")
            dq_b = st.text_input("B", key="dq_b")
            dq_c = st.text_input("C", key="dq_c")
            dq_d = st.text_input("D", key="dq_d")
            dc_a = st.checkbox("A дұрыс", key="dc_a")
            dc_b = st.checkbox("B дұрыс", key="dc_b")
            dc_c = st.checkbox("C дұрыс", key="dc_c")
            dc_d = st.checkbox("D дұрыс", key="dc_d")
            if st.button("Дуэль сұрағын қосу"):
                corrects = []
                if dc_a: corrects.append("A")
                if dc_b: corrects.append("B")
                if dc_c: corrects.append("C")
                if dc_d: corrects.append("D")
                d_qs = st.session_state.app_data["duel_questions"]
                d_qs.append({"id": len(d_qs)+1, "text": dq_text, "options": {"A": dq_a, "B": dq_b, "C": dq_c, "D": dq_d}, "correct": corrects})
                save_data(st.session_state.app_data)
                st.success("Қосылды!")

        with tab4:
            st.subheader("🏆 Оқушыға атақ беру")
            students_list = [u for u, d in users_db.items() if d["role"] == "Student"]
            if students_list:
                sel_student = st.selectbox("Оқушы", students_list)
                badge_input = st.text_input("Атақ атауы")
                if st.button("Атақты беру"):
                    st.session_state.app_data["badges"][sel_student] = badge_input
                    save_data(st.session_state.app_data)
                    st.success("Сақталды!")

        with tab5:
            st.subheader("💬 Ортақ чат")
            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}**: {msg['text']}")
            dir_msg = st.text_input("Хабарлама жазу")
            if st.button("Жіберу"):
                if dir_msg.strip():
                    chat_messages.append({"user": f"{user} (Директор)", "text": dir_msg, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    save_data(st.session_state.app_data)
                    st.rerun()

        with tab6:
            st.subheader("📥 Заявалар")
            for app in st.session_state.app_data.get("applications", []):
                st.write(f"👤 {app['student']}: {app['text']}")

        with tab7:
            st.subheader("⚖️ Аппеляциялар")
            for ap in st.session_state.app_data.get("appeals", []):
                st.write(f"👤 {ap['student']} ({ap['subject']}): {ap['text']}")

        with tab8:
            st.subheader("📊 Нәтижелер")
            results = st.session_state.app_data.get("results", [])
            if results:
                st.dataframe(pd.DataFrame(results))
            else:
                st.info("Әзірге нәтижелер жоқ.")

    elif role == "Teacher":
        st.title("Мұғалім панелі")
        t_sub = st.selectbox("Пән", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика"])
        t_text = st.text_area("Сұрақ мәтіні")
        o_a = st.text_input("A")
        o_b = st.text_input("B")
        o_c = st.text_input("C")
        o_d = st.text_input("D")
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
            st.success("Сәтті қосылды!")

    elif role == "Parent":
        st.title(f"Ата-ана кабинеті: {user}")
        results = st.session_state.app_data.get("results", [])
        if results:
            for r in results:
                st.write(f"Оқушы: **{r['student']}** | Пән: **{r['subject']}** | Ұпай: **{r['score']} / {r['total']}**")
        else:
            st.info("Нәтижелер жоқ.")

    elif role == "Student":
        st.title(f"Оқушы кабинеті: {user}")
        student_direction = users_db[user].get("direction", "Математика - Физика")
        
        my_badge = st.session_state.app_data["badges"].get(user, "")
        if my_badge:
            st.success(f"⭐ Атағыңыз: **{my_badge}**")
            
        tab_s1, tab_s2, tab_s3, tab_s4, tab_s5 = st.tabs(["Профиль", "Тест тапсыру", "Ортақ чат", "Заява", "Аппеляция"])
        
        with tab_s1:
            st.subheader("Жеке мәліметтер")
            st.write(f"**Логин:** {user} | **Бағыт:** {student_direction}")
            my_results = [r for r in st.session_state.app_data.get("results", []) if r['student'] == user]
            if my_results:
                for mr in my_results:
                    st.write(f"- Пән: **{mr['subject']}** | Ұпай: **{mr['score']} / {mr['total']}**")
            else:
                st.info("Тест тапсырған жоқсыз.")

        with tab_s2:
            st.subheader("Тест тапсыру")
            subjects = ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика"]
            sel_sub = st.selectbox("Пәнді таңдаңыз", ["Таңдаңыз..."] + subjects)
            
            if sel_sub != "Таңдаңыз...":
                qs = [q for q in st.session_state.app_data["questions"] if q["subject"] == sel_sub]
                if qs:
                    answers = {}
                    for idx, q in enumerate(qs):
                        st.write(f"**Сұрақ {idx+1}:** {q['text']}")
                        for k, v in q['options'].items():
                            st.write(f"{k}) {v}")
                        answers[q['id']] = st.multiselect("Жауабыңыз", ["A", "B", "C", "D"], key=f"q_{q['id']}")
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
                        st.success(f"Тест аяқталды! Ұпайыңыз: {score} / {len(qs)}")
                else:
                    st.warning("Бұл пән бойынша сұрақтар жоқ.")

        with tab_s3:
            st.subheader("Ортақ чат")
            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}**: {msg['text']}")
            s_msg = st.text_input("Хабарлама жазу")
            if st.button("Жіберу"):
                if s_msg.strip():
                    chat_messages.append({"user": user, "text": s_msg, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    save_data(st.session_state.app_data)
                    st.rerun()

        with tab_s4:
            st.subheader("Заява жазу")
            app_text = st.text_area("Өтінішіңізді жазыңыз")
            if st.button("Заява жіберу"):
                if app_text.strip():
                    st.session_state.app_data["applications"].append({"student": user, "text": app_text, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    save_data(st.session_state.app_data)
                    st.success("Жіберілді!")

        with tab_s5:
            st.subheader("Аппеляция беру")
            ap_sub = st.selectbox("Пән", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика"])
            ap_text = st.text_area("Аппеляция себебі")
            if st.button("Жіберу"):
                if ap_text.strip():
                    st.session_state.app_data["appeals"].append({"student": user, "subject": ap_sub, "text": ap_text, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    save_data(st.session_state.app_data)
                    st.success("Аппеляция жіберілді!")
