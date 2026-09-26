import streamlit as st
from datetime import datetime, timedelta
import random
import json
import os
import pandas as pd

DATA_FILE = "ubt_system_data.json"

def load_data():
    default_data = {
        "users": {
            "director": {"password": "123", "role": "Director", "direction": "Барлығы", "child": "", "limit": None, "blocked": False},
            "teacher1": {"password": "123", "role": "Teacher", "direction": "Барлығы", "child": "", "limit": None, "blocked": False},
            "student1": {"password": "123", "role": "Student", "direction": "Математика - Физика", "child": "", "limit": None, "blocked": False},
            "parent1": {"password": "123", "role": "Parent", "direction": "Барлығы", "child": "student1", "limit": None, "blocked": False},
            "22": {"password": "123", "role": "Student", "direction": "Математика - Физика", "child": "", "limit": None, "blocked": False}
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

st.set_page_config(page_title="T.A.S UBT.kz - Platform", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
    .stApp { background: linear-gradient(135deg, #070913 0%, #110d24 50%, #1c1033 100%); color: #e2e8f0; }
    h1, h2, h3, h4, h5, h6 { color: #d8b4fe !important; font-weight: 700; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, .stTextArea textarea {
        background-color: rgba(30, 27, 75, 0.6) !important; color: #f3e8ff !important; border: 1px solid #7c3aed !important; border-radius: 10px !important;
    }
    .stButton button {
        background: linear-gradient(90deg, #7c3aed 0%, #a855f7 100%) !important; color: #ffffff !important; font-weight: 600; border-radius: 10px; border: none; padding: 0.5rem 1rem;
    }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.title("T.A.S UBT.kz")
    st.markdown("Жүйеге кіру үшін логиніңізді жазыңыз (пароль сұралмайды):")
    
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Кіру"):
        users_db = st.session_state.app_data["users"]
        
        # Егер логин базада болмаса, автоматты түрде Student етіп тіркеп жібереді
        if username and username not in users_db:
            users_db[username] = {"password": "123", "role": "Student", "direction": "Математика - Физика", "child": "", "limit": None, "blocked": False}
            save_data(st.session_state.app_data)
            
        if username in users_db:
            if users_db[username].get("blocked", False):
                st.error("⛔ Бұл аккаунт бұғатталған!")
            else:
                st.session_state.logged_in = True
                st.session_state.current_user = username
                st.rerun()
        else:
            st.error("Логінді енгізіңіз!")

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
        tab1, tab2, tab3 = st.tabs(["Қолданушылар", "Сұрақтар", "Қолданушы қосу"])
        
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
            st.subheader("📚 Сұрақтарды басқару")
            q_sub = st.selectbox("Пән", ["Математикалық сауаттылық", "Қазақстан тарихы", "Математика", "Физика"])
            q_text = st.text_area("Сұрақ мәтіні")
            if st.button("Қосу"):
                qs = st.session_state.app_data["questions"]
                qs.append({"id": len(qs)+1, "subject": q_sub, "text": q_text, "options": {"A": "1", "B": "2", "C": "3", "D": "4"}, "correct": ["A"]})
                save_data(st.session_state.app_data)
                st.success("Қосылды!")

        with tab3:
            st.subheader("🔑 Қолданушы қосу")
            new_u = st.text_input("Логин", key="add_u")
            new_r = st.selectbox("Рөл", ["Student", "Parent", "Teacher", "Director"], key="add_r")
            if st.button("Жасау", key="add_btn"):
                if new_u and new_u not in users_db:
                    users_db[new_u] = {"password": "123", "role": new_r, "direction": "Барлығы", "child": "", "limit": None, "blocked": False}
                    save_data(st.session_state.app_data)
                    st.success("Сәтті жасалды!")

    else:
        st.title(f"Қош келдіңіз, {user} ({role})!")
        st.write("Бұл оқушы/қолданушы кабинеті.")
        sel_sub = st.selectbox("Пәнді таңдаңыз", ["Математикалық сауаттылық", "Қазақстан тарихы", "Математика", "Физика"])
        qs = [q for q in st.session_state.app_data["questions"] if q["subject"] == sel_sub]
        if qs:
            for idx, q in enumerate(qs):
                st.write(f"{idx+1}. {q['text']}")
        else:
            st.info("Бұл пәнге әзірге сұрақ қосылмаған.")
