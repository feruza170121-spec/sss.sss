import streamlit as st
from datetime import datetime, timedelta
import random
import json
import os
import requests
import urllib.parse
import pandas as pd
import time

DATA_FILE = "ubt_system_data.json"

def load_data():
    default_data = {
        "users": {
            "director": {"password": "123", "role": "Director", "direction": "Барлығы", "class_level": 11, "blocked": False},
            "teacher1": {"password": "123", "role": "Teacher", "direction": "Барлығы", "class_level": 11, "blocked": False},
            "student1": {"password": "123", "role": "Student", "direction": "Математика - Физика", "class_level": 10, "blocked": False},
            "student2": {"password": "123", "role": "Student", "direction": "Математика - Физика", "class_level": 11, "blocked": False},
            "parent1": {"password": "123", "role": "Parent", "direction": "Барлығы", "class_level": 11, "blocked": False}
        },
        "questions": [],
        "teams": {}, 
        "results": [],
        "chat_messages": [],
        "direct_messages": {}, 
        "bans": {}, 
        "team_warning_accepted": {} 
    }
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                loaded = json.load(f)
                for key in default_data:
                    if key not in loaded:
                        loaded[key] = default_data[key]
                for u in loaded["users"]:
                    if "class_level" not in loaded["users"][u]:
                        loaded["users"][u]["class_level"] = 10
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

BAD_WORDS = ["ботк", "сұка", "обал", "шайтан", "ақымақ", "есек", "сорлы"]

def check_user_ban(username):
    bans = st.session_state.app_data["bans"]
    if username in bans:
        unban_str = bans[username]["end_time"]
        unban_time = datetime.strptime(unban_str, "%Y-%m-%d %H:%M:%S")
        if datetime.now() < unban_time:
            return True, unban_str
        else:
            del bans[username]
            save_data(st.session_state.app_data)
    return False, ""

def ban_entire_team(team_name, reason="Чит қолданылды"):
    teams = st.session_state.app_data["teams"]
    bans = st.session_state.app_data["bans"]
    if team_name in teams:
        members = [teams[team_name]["captain"]] + teams[team_name]["members"]
        unban_time = datetime.now() + timedelta(days=20)
        unban_str = unban_time.strftime("%Y-%m-%d %H:%M:%S")
        for m in members:
            bans[m] = {"end_time": unban_str, "reason": reason}
        save_data(st.session_state.app_data)

st.set_page_config(page_title="UBT.kz - Турнирлік жүйе", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #00ff66; }
    h1, h2, h3, h4, h5, h6, p, label, span, .stMarkdown { color: #00ff66 !important; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background-color: #1a1c23 !important; color: #00ff66 !important; border: 1px solid #00ff66 !important;
    }
    .stButton button { background-color: #00ff66 !important; color: #0e1117 !important; font-weight: bold; border-radius: 5px; }
    .stButton button:hover { background-color: #00cc55 !important; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.title("🔐 UBT.kz Secure Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login"):
        users_db = st.session_state.app_data["users"]
        if username in users_db and users_db[username]["password"] == password:
            is_banned, b_time = check_user_ban(username)
            if is_banned and username != "director":
                st.error(f"⛔ Бұл аккаунт банға кеткен! Бан бітетін уақыты: {b_time}. Директорға өтініш жазыңыз.")
                st.stop()
            st.session_state.logged_in = True
            st.session_state.current_user = username
            st.rerun()
        else:
            st.error("Қате логин немесе пароль!")
else:
    user = st.session_state.current_user
    users_db = st.session_state.app_data["users"]
    role = users_db[user]["role"]
    
    if role != "Director":
        is_banned, b_time = check_user_ban(user)
        if is_banned:
            st.title(f"⛔ Сіздің аккаунтыңыз банға ұшырады!")
            st.error(f"Бан уақыты: {b_time}")
            st.warning("Директорға төмендегі арнайы бөлім арқылы хат жазып, өтініш бере аласыз.")
            
            st.subheader("📩 Директорға өтініш (Заява директора)")
            dm_dict = st.session_state.app_data["direct_messages"]
            if user not in dm_dict:
                dm_dict[user] = []
            
            for msg in dm_dict[user]:
                st.write(f"**{msg['sender']}** ({msg['time']}): {msg['text']}")
                
            with st.form("banned_dm_form", clear_on_submit=True):
                txt = st.text_input("Директорға хат жазу:")
                if st.form_submit_button("Жіберу"):
                    if txt:
                        dm_dict[user].append({"sender": user, "text": txt, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                        save_data(st.session_state.app_data)
                        st.success("Өтініш жіберілді!")
                        st.rerun()
            
            if st.button("Жүйеден шығу"):
                st.session_state.logged_in = False
                st.session_state.current_user = None
                st.rerun()
            st.stop()

    st.sidebar.title(f"Қош келдіңіз, {user}!")
    st.sidebar.text(f"Рөлі: {role}")
    
    if st.sidebar.button("Жүйеден шығу"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.rerun()

    if role == "Director":
        st.title("👑 Директордың басқару панелі")
        tab1, tab2, tab3 = st.tabs(["Қолданушылар & Бандарды басқару", "Сұрақтар қосу", "Оқушылардың өтініштері"])
        
        with tab1:
            st.subheader("⚙️ Банға кеткен қолданушылар / командалар")
            bans = st.session_state.app_data["bans"]
            if bans:
                for b_user, b_info in list(bans.items()):
                    st.write(f"👤 **{b_user}** | Себебі: {b_info['reason']} | Бітетін уақыты: {b_info['end_time']}")
                    if st.button(f"Банды алу (Unban): {b_user}", key=f"unban_{b_user}"):
                        del bans[b_user]
                        save_data(st.session_state.app_data)
                        st.success(f"{b_user} баннан шығарылды!")
                        st.rerun()
            else:
                st.info("Қазір банға кеткендер жоқ.")
                
        with tab2:
            st.subheader("📚 Сұрақ қосу")
            with st.form("dir_q"):
                q_sub = st.selectbox("Пән", ["Математикалық сауаттылық", "Математика", "Физика", "Биология", "Химия"])
                q_text = st.text_area("Сұрақ мәтіні")
                opt_a = st.text_input("A")
                opt_b = st.text_input("B")
                opt_c = st.text_input("C")
                opt_d = st.text_input("D")
                c_a = st.checkbox("A дұрыс")
                c_b = st.checkbox("B дұрыс")
                c_c = st.checkbox("C дұрыс")
                c_d = st.checkbox("D дұрыс")
                if st.form_submit_button("Қосу"):
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
            st.subheader("📩 Оқушылардан келген жеке өтініштер (Заява директора)")
            dm_dict = st.session_state.app_data["direct_messages"]
            if dm_dict:
                for student_name, msgs in dm_dict.items():
                    with st.expander(f"Өтініш беруші: {student_name} ({len(msgs)} хат)"):
                        for m in msgs:
                            st.write(f"**{m['sender']}**: {m['text']} *({m['time']})*")
                        
                        reply_key = f"reply_{student_name}"
                        with st.form(reply_key):
                            rep_text = st.text_input("Жауап жазу:")
                            if st.form_submit_button("Жауап жіберу"):
                                if rep_text:
                                    msgs.append({"sender": "Директор", "text": rep_text, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                                    save_data(st.session_state.app_data)
                                    st.success("Жауап жіберілді!")
                                    st.rerun()
            else:
                st.info("Әзірге өтініштер жоқ.")

    elif role == "Student":
        st.title(f"🎓 Оқушы кабинеті: {user}")
        student_dir = users_db[user].get("direction", "Математика - Физика")
        student_class = users_db[user].get("class_level", 10)
        
        tab_s1, tab_s2, tab_s3, tab_s4, tab_s5 = st.tabs(["🎯 Тест", "⚔️ 4x4 Турнир", "💬 Ортақ чат", "📩 Директорға өтініш", "👤 Профиль"])
        
        with tab_s1:
            st.subheader("🎯 Пәндік тест")
            qs = st.session_state.app_data["questions"]
            if qs:
                with st.form("exam_form"):
                    answers = {}
                    for idx, q in enumerate(qs):
                        st.markdown(f"**Сұрақ {idx+1}**: {q['text']}")
                        for k, v in q['options'].items():
                            st.write(f"{k}) {v}")
                        ans = st.multiselect("Жауап", ["A", "B", "C", "D"], key=f"q_{q['id']}")
                        answers[q['id']] = ans
                        st.divider()
                    
                    if st.form_submit_button("Тестті аяқтау"):
                        score = 0
                        for q in qs:
                            if set(answers.get(q['id'], [])) == set(q['correct']):
                                score += 1
                        st.success(f"Нәтиже: {score} / {len(qs)}")
            else:
                st.warning("Сұрақтар жоқ.")

        with tab_s2:
            st.subheader("⚔️ 4x4 Командалық турнир")
            
            warnings_accepted = st.session_state.app_data["team_warning_accepted"]
            if not warnings_accepted.get(user, False):
                st.markdown("""
                    <div style="background-color: #ff2a2a22; border: 2px solid #ff2a2a; padding: 20px; border-radius: 10px; text-align: center;">
                        <h2 style="color: #ff2a2a !important;">⚠️ МАҢДЫЗДЫ ЕРЕЖЕ ЖӘНЕ ЕСКЕРТУ!</h2>
                        <p style="font-size: 18px; font-weight: bold; color: #ff2a2a !important;">
                        КОМАНДАЛЫҚ ТЕСТ ЖӘНЕ ТУРНИР КЕЗІНДЕ ЕГЕР ҚАНДАЙ ДА БІР ЧИТ НЕМЕСЕ АЛДАУ ТӘСІЛІ ҚОЛДАНЫЛСА, 
                        СОЛ КОМАНДАНЫҢ БАРЛЫҚ МҮШЕЛЕРІНЕ БІРДЕЙ <b>20 КҮНДІК БАН</b> БЕРІЛЕДІ!
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔴 ОҚЫДЫМ, ТҮСІНДІМ ЖӘНЕ КЕЛІСЕМІН"):
                    warnings_accepted[user] = True
                    save_data(st.session_state.app_data)
                    st.rerun()
                st.stop()

            teams = st.session_state.app_data["teams"]
            my_current_team = None
            for t_name, t_info in teams.items():
                if user == t_info["captain"] or user in t_info["members"]:
                    my_current_team = t_name
                    break
            
            if my_current_team:
                st.success(f"✅ Сіз **{my_current_team}** командасындасыз!")
                t_data = teams[my_current_team]
                st.write(f"👑 Капитан: {t_data['captain']}")
                st.write(f"👥 Мүшелері ({len(t_data['members'])}/4): {', '.join(t_data['members'])}")
                
                if st.button("🚪 Командадан шығу"):
                    if user == t_data["captain"]:
                        del teams[my_current_team]
                    else:
                        t_data["members"].remove(user)
                    save_data(st.session_state.app_data)
                    st.warning("Сіз командадан шықтыңыз!")
                    st.rerun()
            else:
                st.write("### Жаңа команда ашу немесе қосылу")
                with st.form("create_team"):
                    new_t_name = st.text_input("Команда атауы")
                    if st.form_submit_button("Команда құру (Капитан болу)"):
                        if new_t_name and new_t_name not in teams:
                            teams[new_t_name] = {
                                "captain": user,
                                "direction": student_dir,
                                "class_level": student_class,
                                "members": [user]
                            }
                            save_data(st.session_state.app_data)
                            st.success("Команда құрылды!")
                            st.rerun()
                        else:
                            st.error("Қате атау.")
                
                st.divider()
                st.write("### Қолжетімді командалар:")
                if teams:
                    for t_name, t_data in teams.items():
                        st.write(f"🛡️ **{t_name}** | Капитан: {t_data['captain']} | Сынып: {t_data['class_level']} | Мүшелер: {len(t_data['members'])}/4")
                        if student_class > t_data["class_level"]:
                            st.caption("⚠️ Сыныбыңыз үлкен болғандықтан қосыла алмайсыз.")
                        elif len(t_data["members"]) >= 4:
                            st.caption("🔒 Команда толы.")
                        else:
                            if st.button(f"Қосылу: {t_name}", key=f"join_{t_name}"):
                                t_data["members"].append(user)
                                save_data(st.session_state.app_data)
                                st.success("Қосылдыңыз!")
                                st.rerun()
                else:
                    st.info("Командалар жоқ.")

        with tab_s3:
            st.subheader("💬 Ортақ чат")
            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}**: {msg['text']} *({msg['time']})*")
                
            with st.form("chat_form", clear_on_submit=True):
                txt = st.text_input("Хабарлама жазу:")
                if st.form_submit_button("Жіберу"):
                    if txt:
                        chat_messages.append({"user": user, "text": txt, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                        save_data(st.session_state.app_data)
                        st.rerun()

        with tab_s4:
            st.subheader("📩 Директорға өтініш (Заява директора)")
            st.info("Бұл жерде жазған хаттарыңызды тек сіз бен Директор ғана көре алады.")
            dm_dict = st.session_state.app_data["direct_messages"]
            if user not in dm_dict:
                dm_dict[user] = []
                
            for msg in dm_dict[user]:
                st.write(f"**{msg['sender']}** ({msg['time']}): {msg['text']}")
                
            with st.form("student_dm_form", clear_on_submit=True):
                dm_txt = st.text_input("Директорға хат немесе өтініш жазу:")
                if st.form_submit_button("Жіберу"):
                    if dm_txt:
                        dm_dict[user].append({"sender": user, "text": dm_txt, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                        save_data(st.session_state.app_data)
                        st.success("Өтініш директорға сәтті жіберілді!")
                        st.rerun()

        with tab_s5:
            st.subheader("👤 Профиль")
            st.write(f"**Логин:** {user}")
            st.write(f"**Бағыт:** {student_dir}")
            st.write(f"**Сынып:** {student_class}-сынып")

    elif role == "Teacher":
        st.title(f"🏫 Мұғалім кабинеті: {user}")
        st.write("Мұғалім панелі жұмыс істеп тұр.")

    elif role == "Parent":
        st.title(f"👪 Ата-ана кабинеті: {user}")
        st.write("Балаңыздың нәтижелерін бақылай аласыз.")
