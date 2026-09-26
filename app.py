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
            "student2": {"password": "123", "role": "Student", "direction": "Биология - Химия", "limit": None, "blocked": False}
        },
        "questions": [],
        "duel_questions": [], 
        "login_logs": [],
        "results": [],
        "feedback": [],
        "friends": {},
        "notifications": {},
        "duels": [],
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
                if "duel_questions" not in loaded:
                    loaded["duel_questions"] = []
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

def send_whatsapp_alert(phone, message):
    if not phone:
        return
    try:
        encoded_message = urllib.parse.quote(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_message}&apikey=free"
        requests.get(url, timeout=3)
    except Exception:
        pass

st.set_page_config(page_title="UBT.kz - Secure Platform", layout="centered")

st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #00ff66;
    }
    h1, h2, h3, h4, h5, h6, p, label, span, .stMarkdown {
        color: #00ff66 !important;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background-color: #1a1c23 !important;
        color: #00ff66 !important;
        border: 1px solid #00ff66 !important;
    }
    .stButton button {
        background-color: #00ff66 !important;
        color: #0e1117 !important;
        font-weight: bold;
        border-radius: 5px;
    }
    .stButton button:hover {
        background-color: #00cc55 !important;
        color: #0e1117 !important;
    }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.title("🔐 UBT.kz Secure Login")
    
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login"):
        now = datetime.now()
        users_db = st.session_state.app_data["users"]
        
        if username in users_db and users_db[username].get("blocked", False):
            st.error("Бұл аккаунт директор тарапынан бұғатталған!")
            st.stop()
        
        if username in st.session_state.blocked_users:
            unblock_time = st.session_state.blocked_users[username]
            if now < unblock_time:
                remaining = int((unblock_time - now).total_seconds() / 60)
                st.error(f"Бұл аккаунт 10 рет қате енгізілгені үшін бұғатталған. {remaining} минуттан кейін қайталап көріңіз.")
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
        st.rerun()

    if role == "Director":
        st.title("👑 Директордың басқару панелі")
        whatsapp_phone_saved = st.session_state.app_data["settings"].get("whatsapp_phone", "")
        
        if not whatsapp_phone_saved:
            st.warning("⚠️ Назар аударыңыз! Жүйені толық пайдалану үшін төменде WhatsApp нөміріңізді міндетті түрде жазып сақтауыңыз қажет.")
            phone_input = st.text_input("WhatsApp нөміріңіз (мысалы: 77012345678)", key="initial_whatsapp_input")
            if st.button("WhatsApp нөмірін сақтау"):
                if phone_input:
                    st.session_state.app_data["settings"]["whatsapp_phone"] = phone_input
                    save_data(st.session_state.app_data)
                    st.success("Сақталды!")
                    st.rerun()
            st.stop()

        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "Қолданушылар", "Мұғалім Лимиттері", "Сұрақтар", "⚔️ Дуэль баптаулары", "📊 Статистика", "💬 Шағымдар", "Қолданушы қосу", "Баптаулар"
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
            with st.form("dir_q"):
                q_sub = st.selectbox("Пән", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика", "Биология", "Химия", "Ағылшын тілі", "Дүние жүзі тарихы", "География"])
                q_text = st.text_area("Сұрақ")
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
                    new_id = max([q["id"] for q in qs], default=0) + 1
                    qs.append({"id": new_id, "subject": q_sub, "text": q_text, "options": {"A": opt_a, "B": opt_b, "C": opt_c, "D": opt_d}, "correct": corrects})
                    save_data(st.session_state.app_data)
                    st.success("Сәтті қосылды!")

        with tab4:
            st.subheader("⚔️ Дуэль сұрақтары мен уақытын басқару")
            st.write("Мұнда тек оқушылардың дуэль сайысына арналған бөлек сұрақтар мен уақытты (минут) баптай аласыз.")
            
            with st.form("duel_settings_form"):
                new_duel_timer = st.number_input("Дуэль уақыты (минут)", min_value=1, max_value=60, value=st.session_state.app_data["settings"].get("duel_timer", 3))
                if st.form_submit_button("Дуэль уақытын сақтау"):
                    st.session_state.app_data["settings"]["duel_timer"] = new_duel_timer
                    save_data(st.session_state.app_data)
                    st.success(f"Дуэль уақыты {new_duel_timer} минут етіп сақталды!")
            
            st.divider()
            st.subheader("➕ Дуэльге жеке сұрақ қосу")
            with st.form("duel_q_form"):
                dq_text = st.text_area("Дуэль сұрағының мәтіні")
                dq_a = st.text_input("A нұсқасы", key="dq_a")
                dq_b = st.text_input("B нұсқасы", key="dq_b")
                dq_c = st.text_input("C нұсқасы", key="dq_c")
                dq_d = st.text_input("D нұсқасы", key="dq_d")
                dc_a = st.checkbox("A дұрыс", key="dc_a")
                dc_b = st.checkbox("B дұрыс", key="dc_b")
                dc_c = st.checkbox("C дұрыс", key="dc_c")
                dc_d = st.checkbox("D дұрыс", key="dc_d")
                
                if st.form_submit_button("Дуэль сұрағын қосу"):
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

            st.divider()
            st.subheader("📋 Қосылған дуэль сұрақтарының тізімі")
            d_qs = st.session_state.app_data.get("duel_questions", [])
            if d_qs:
                for idx, dq in enumerate(d_qs):
                    st.write(f"**{idx+1}-сұрақ:** {dq['text']}")
                    for opt_k, opt_v in dq['options'].items():
                        st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;{opt_k}) {opt_v}")
                    st.write(f"Дұрыс жауап(тар): **{', '.join(dq['correct'])}**")
                    
                    if st.button("Бұл сұрақты өшіру", key=f"del_dq_{dq['id']}"):
                        st.session_state.app_data["duel_questions"] = [q for q in d_qs if q['id'] != dq['id']]
                        save_data(st.session_state.app_data)
                        st.success("Дуэль сұрағы өшірілді!")
                        st.rerun()
                    st.divider()
            else:
                st.info("Әзірге дуэль сұрақтары қосылмаған.")

        with tab5:
            st.subheader("📊 Барлық оқушылар нәтижелері мен рейтингі")
            results = st.session_state.app_data.get("results", [])
            if results:
                df = pd.DataFrame(results)
                st.dataframe(df)
                if st.session_state.app_data["settings"].get("allow_export", False):
                    st.download_button("Excel жүктеу", df.to_csv(index=False).encode('utf-8'), "results.csv", "text/csv")
            else:
                st.write("Нәтижелер жоқ.")

        with tab6:
            st.subheader("💬 Шағымдар мен хаттар")
            for fb in reversed(st.session_state.app_data.get("feedback", [])):
                st.write(f"**{fb['user']}**: {fb['message']} ({fb['time']})")

        with tab7:
            st.subheader("🔑 Жаңа қолданушы қосу (Бағытымен)")
            new_u = st.text_input("Жаңа логин")
            new_p = st.text_input("Пароль", type="password")
            new_r = st.selectbox("Рөл", ["Student", "Teacher"])
            
            new_dir = "Барлығы"
            if new_r == "Student":
                new_dir = st.selectbox("Оқушының бағытын таңдаңыз", ["Математика - Физика", "Биология - Химия", "Ағылшын - Тарих", "География - Математика"])
            
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
                    st.success(f"Жаңа {new_r} сәтті жасалды! Бағыты: {new_dir}")
                else:
                    st.error("Бұл логин бос емес немесе қате.")

        with tab8:
            st.subheader("⚙️ Жүйелік баптаулар")
            st.session_state.app_data["settings"]["timer_enabled"] = st.checkbox("Таймер қосу", value=st.session_state.app_data["settings"]["timer_enabled"])
            st.session_state.app_data["settings"]["timer_duration"] = st.number_input("Уақыт (мин)", value=st.session_state.app_data["settings"]["timer_duration"])
            st.session_state.app_data["settings"]["allow_export"] = st.checkbox("📁 Экспортқа (Excel/PDF) рұқсат беру", value=st.session_state.app_data["settings"].get("allow_export", False))
            save_data(st.session_state.app_data)
            st.success("Сақталды!")

    elif role == "Teacher":
        st.title("📚 Мұғалім панелі")
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

    elif role == "Student":
        st.title(f"🎓 Оқушы кабинеті: {user}")
        student_direction = users_db[user].get("direction", "Математика - Физика")
        st.info(f"📌 Сіздің бекітілген бағытыңыз: **{student_direction}**")
        
        tab_s1, tab_s2, tab_s3, tab_s4, tab_s5 = st.tabs(["👤 Менің профайлым", "🏆 Жалпы рейтинг & Салыстыру", "⚔️ Тест тапсыру", "👥 Достар & Дуэль", "📬 Хабарландырулар"])
        
        with tab_s1:
            st.subheader("👤 Жеке профиль статистикасы")
            results = st.session_state.app_data.get("results", [])
            my_results = [r for r in results if r['student'] == user]
            
            st.write(f"**Аты-жөні (Логині):** {user}")
            st.write(f"**Таңдалған бағыт:** {student_direction}")
            st.write(f"**Тапсырған тест саны:** {len(my_results)}")
            
            if my_results:
                total_score = sum([r['score'] for r in my_results])
                total_possible = sum([r['total'] for r in my_results])
                avg_percentage = (total_score / total_possible * 100) if total_possible > 0 else 0
                st.write(f"**Жалпы жинаған ұпайы:** {total_score}")
                st.write(f"**Орташа көрсеткіш (Процент):** {avg_percentage:.1f}%")
            else:
                st.info("Әзірге тест тапсырған жоқсыз.")

        with tab_s2:
            st.subheader("🏆 Жалпы рейтинг және оқушыларды салыстыру")
            results = st.session_state.app_data.get("results", [])
            
            student_stats = {}
            for r in results:
                s = r['student']
                if s not in student_stats:
                    student_stats[s] = {"total_score": 0, "total_possible": 0, "tests": 0}
                student_stats[s]["total_score"] += r['score']
                student_stats[s]["total_possible"] += r['total']
                student_stats[s]["tests"] += 1
            
            ranking_list = []
            for s, data in student_stats.items():
                pct = (data["total_score"] / data["total_possible"] * 100) if data["total_possible"] > 0 else 0
                ranking_list.append({"student": s, "score": data["total_score"], "percentage": pct, "tests": data["tests"]})
            
            ranking_list = sorted(ranking_list, key=lambda x: x['score'], reverse=True)
            
            if ranking_list:
                st.write("### 🥇 Сайттағы оқушылардың топ тізімі:")
                for idx, item in enumerate(ranking_list):
                    place = idx + 1
                    is_me = " (Сіз)" if item['student'] == user else ""
                    st.write(f"**{place}-орын:** {item['student']}{is_me} — Ұпай: {item['score']} | Процент: **{item['percentage']:.1f}%** (Тест саны: {item['tests']})")
                
                st.divider()
                st.subheader("📊 Сіздің басқа оқушылармен пайыздық салыстыруыңыз:")
                my_data = next((item for item in ranking_list if item['student'] == user), None)
                if my_data:
                    my_rank = ranking_list.index(my_data) + 1
                    st.success(f"Сіз қазіргі уақытта сайтта **{my_rank}-орындасыз**! Проценттік көрсеткішіңіз: **{my_data['percentage']:.1f}%**")
                    
                    for item in ranking_list:
                        if item['student'] != user:
                            diff = my_data['percentage'] - item['percentage']
                            status = f"жоғары (+{diff:.1f}%)" if diff >= 0 else f"төмен ({diff:.1f}%)"
                            st.write(f"- {item['student']} ({item['percentage']:.1f}%) қарағанда сіздің көрсеткішіңіз **{status}**.")
            else:
                st.info("Әзірге ешқандай оқушы тест тапсырмаған.")

        with tab_s3:
            st.subheader("🎯 Жаңа тесттер мен тапсыру алаңы")
            if not st.session_state.test_submitted:
                st.write(f"Сіздің бағытыңыз бойынша тапсыруға болатын пәндер:")
                
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
                        st.info(f"Бұл пән бойынша жаңадан қосылған сұрақтар саны: {len(qs)}")
                        with st.form("exam_form"):
                            answers = {}
                            for idx, q in enumerate(qs):
                                st.write(f"**Сұрақ {idx+1}:** {q['text']}")
                                for k, v in q['options'].items():
                                    st.write(f"{k}) {v}")
                                ans = st.multiselect("Жауапты таңдаңыз", ["A", "B", "C", "D"], key=f"q_{q['id']}")
                                answers[q['id']] = ans
                                st.divider()
                            
                            if st.form_submit_button("Тестті аяқтау"):
                                score = 0
                                for q in qs:
                                    if set(answers.get(q['id'], [])) == set(q['correct']):
                                        score += 1
                                
                                st.session_state.app_data["results"].append({
                                    "student": user, "subject": sel_sub, "score": score, "total": len(qs), "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                                })
                                save_data(st.session_state.app_data)
                                st.session_state.test_submitted = True
                                st.session_state.current_test_results = {"score": score, "total": len(qs)}
                                st.rerun()
                    else:
                        st.warning("Бұл пән бойынша әзірге жаңа тесттер жоқ.")
            else:
                res = st.session_state.current_test_results
                st.success(f"Тест сәтті аяқталды! Нәтижеңіз: {res['score']} / {res['total']}")
                if st.button("Басқа тестке өту"):
                    st.session_state.test_submitted = False
                    st.rerun()

        with tab_s4:
            st.subheader("👥 Достар және Дуэль жүйесі")
            duel_timer_val = st.session_state.app_data["settings"].get("duel_timer", 3)
            duel_questions = st.session_state.app_data.get("duel_questions", [])
            
            st.info(f"⚡ Дуэль ережесі: Директор белгілеген бөлек дуэль сұрақтары беріледі. Уақыт лимиті: **{duel_timer_val} минут**.")
            
            friends_db = st.session_state.app_data["friends"]
            notif_db = st.session_state.app_data["notifications"]
            
            my_friends = friends_db.get(user, [])
            st.write(f"**Достарыңыз:** {', '.join(my_friends) if my_friends else 'Достар тізімі бос.'}")
            
            friend_input = st.text_input("Достыққа шақыру үшін логин жазыңыз:")
            if st.button("Дос болуға шақыру жіберу"):
                if friend_input and friend_input in users_db and friend_input != user:
                    if friend_input not in notif_db:
                        notif_db[friend_input] = []
                    notif_db[friend_input].append(f"🔔 {user} сізді дос болуға шақырды!")
                    save_data(st.session_state.app_data)
                    st.success("Шақыру жіберілді!")
                else:
                    st.error("Қате логин.")
            
            st.divider()
            if duel_questions:
                st.write("⚔️ **Дуэль сайысын бастау** (Директордың жеке дуэль сұрақтары арқылы):")
                duel_opponent = st.selectbox("Қарсыласты таңдаңыз", ["Таңдаңыз..."] + my_friends)
                if duel_opponent != "Таңдаңыз..." and st.button("Дуэльге кірісу"):
                    st.success(f"{duel_opponent}-мен дуэль басталды! Уақыт: {duel_timer_val} минут. Сұрақтар саны: {len(duel_questions)}")
            else:
                st.warning("Әзірге директор дуэль сұрақтарын қосқан жоқ.")

        with tab_s5:
            st.subheader("📬 Хабарландырулар және Шақырулар")
            notif_db = st.session_state.app_data["notifications"]
            my_notifs = notif_db.get(user, [])
            
            if my_notifs:
                for n in reversed(my_notifs):
                    st.info(n)
            else:
                st.write("Жаңа хабарландырулар жоқ.")
