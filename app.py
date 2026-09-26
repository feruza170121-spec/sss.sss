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
        "badges": {}, # Оқушы атақтары/марапаттары (тек директор береді)
        "chat_messages": [], # Чат хабарламалары
        "bans": {}, # Чаттан банға кеткендер: {username: unban_datetime_str}
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
                if "badges" not in loaded:
                    loaded["badges"] = {}
                if "chat_messages" not in loaded:
                    loaded["chat_messages"] = []
                if "bans" not in loaded:
                    loaded["bans"] = {}
                if "duel_questions" not in loaded:
                    loaded["duel_questions"] = []
                if "duel_results" not in loaded:
                    loaded["duel_results"] = []
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

# Боқтық сөздер тізімі (автоматты түрде 15 күнге банға жіберу үшін)
BAD_WORDS = ["ботк", "сұка", "обал", "шайтан", "тексерілмеген_сөз", "қарапайым_боқтық", "ақымақ", "есек", "мұрын", "құрт", "сорлы"] 
# (Өзіңіз қалаған боқтық сөздерді осы тізімге қосып немесе толықтыра аласыз)

def check_bad_words_and_ban(username, text):
    text_lower = text.lower()
    for word in BAD_WORDS:
        if word in text_lower:
            # 15 күнге бан беру
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

        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
            "Қолданушылар", "Мұғалім Лимиттері", "Сұрақтар", "⚔️ Дуэль", "🏆 Атақтар беру", "💬 Чат & Бан", "📊 Статистика", "Қолданушы қосу", "Баптаулар"
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
            with st.form("duel_settings_form"):
                new_duel_timer = st.number_input("Дуэль уақыты (минут)", min_value=1, max_value=60, value=st.session_state.app_data["settings"].get("duel_timer", 3))
                if st.form_submit_button("Дуэль уақытын сақтау"):
                    st.session_state.app_data["settings"]["duel_timer"] = new_duel_timer
                    save_data(st.session_state.app_data)
                    st.success(f"Дуэль уақыты {new_duel_timer} минут етіп сақталды!")
            
            st.divider()
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

        with tab5:
            st.subheader("🏆 Оқушыларға атақ (Badge) беру немесе алып тастау")
            st.write("Тек директор оқушыға арнайы атақ бере алады (Мысалы: 🥇 *Математика королі*, 🧠 *Үздік тапқыр*, т.б.)")
            
            students_list = [u for u, d in users_db.items() if d["role"] == "Student"]
            if students_list:
                sel_student = st.selectbox("Оқушыны таңдаңыз", students_list)
                current_badge = st.session_state.app_data["badges"].get(sel_student, "")
                st.write(str(f"Қазіргі атағы: **{currentBadge if (currentBadge := current_badge) else 'Жоқ'}**"))
                
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
                            st.warning(f"{sel_student} оқушысының атағы алынып тасталды!")
                            st.rerun()

        with tab6:
            st.subheader("💬 Ортақ чат бан жүйесі (Директор басқаруы)")
            st.write("Мұнда чатта боқтық жазған немесе ереже бұзған қолданушылардың 15 күндік бан тізімін басқара аласыз.")
            
            bans_db = st.session_state.app_data["bans"]
            now_dt = datetime.now()
            
            active_bans = {}
            for u_ban, b_time_str in bans_db.items():
                b_dt = datetime.strptime(b_time_str, "%Y-%m-%d %H:%M:%S")
                if now_dt < b_dt:
                    active_bans[u_ban] = b_dt
                
            if active_bans:
                st.write("### Қазір банға түскендер:")
                for b_user, b_expire in active_bans.items():
                    col_u1, col_u2 = st.columns([3, 1])
                    with col_u1:
                        st.write(f"🔴 **{b_user}** — Банның бітетін уақыты: {b_expire.strftime('%Y-%m-%d %H:%M')}")
                    with col_u2:
                        if st.button("Банды алу (Unban)", key=f"unban_{b_user}"):
                            del st.session_state.app_data["bans"][b_user]
                            save_data(st.session_state.app_data)
                            st.success(f"{b_user} баннан шығарылды!")
                            st.rerun()
            else:
                st.info("Қазір белсенді бан алған қолданушылар жоқ.")

        with tab7:
            st.subheader("📊 Барлық оқушылар нәтижелері мен графикасы")
            results = st.session_state.app_data.get("results", [])
            if results:
                df = pd.DataFrame(results)
                st.dataframe(df)
                st.bar_chart(df.set_index("student")[["score"]])
            else:
                st.info("Әзірге тест нәтижелері жоқ.")

        with tab8:
            st.subheader("🔑 Жаңа қолданушы қосу (Студент, Мұғалім, Ата-ана)")
            new_u = st.text_input("Жаңа логин")
            new_p = st.text_input("Пароль", type="password")
            new_r = st.selectbox("Рөл", ["Student", "Parent", "Teacher"])
            
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
                    st.success(f"Жаңа {new_r} сәтті жасалды!")
                else:
                    st.error("Бұл логин бос емес немесе қате.")

        with tab9:
            st.subheader("⚙️ Жүйелік баптаулар")
            st.session_state.app_data["settings"]["timer_enabled"] = st.checkbox("Таймер қосу", value=st.session_state.app_data["settings"]["timer_enabled"])
            st.session_state.app_data["settings"]["timer_duration"] = st.number_input("Уақыт (мин)", value=st.session_state.app_data["settings"]["timer_duration"])
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

    elif role == "Parent":
        st.title(f"👪 Ата-ана кабинеті: {user}")
        st.info("📌 Мұнда сіз оқушылардың тест нәтижелерін, қатемен жұмыстарын бақылап, жалпы ортақ чатта сөйлесе аласыз.")
        
        tab_p1, tab_p2 = st.tabs(["📊 Балалардың нәтижелері мен қателері", "💬 Жалпы чат (Талқылау)"])
        
        with tab_p1:
            st.subheader("📈 Барлық оқушылардың нәтижелері мен қатемен жұмыстары")
            results = st.session_state.app_data.get("results", [])
            if results:
                for r in reversed(results):
                    st.write(f"👤 Оқушы: **{r['student']}** | Пән: **{r['subject']}** | Ұпай: **{r['score']} / {r['total']}** ({r['date']})")
            else:
                st.info("Әзірге тест нәтижелері жоқ.")
                
        with tab_p2:
            st.subheader("💬 Ортақ талқылау чаты (Ата-аналар, мұғалімдер, оқушылар)")
            bans = st.session_state.app_data.get("bans", {})
            is_banned = False
            if user in bans:
                b_until = datetime.strptime(bans[user], "%Y-%m-%d %H:%M:%S")
                if datetime.now() < b_until:
                    is_banned = True
                    st.error(f"⛔ Сіз ереже бұзғаныңыз үшін чаттан банға түстік! Банның аяқталу уақыты: {b_until}")
            
            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}** ({msg['time']}): {msg['text']}")
                
            if not is_banned:
                with st.form("parent_chat_form", clear_on_submit=True):
                    msg_text = st.text_input("Хабарлама жазу (Қателерді талқылау):")
                    if st.form_submit_button("Жіберу"):
                        if msg_text:
                            # Боқтыққа тексеру
                            if check_bad_words_and_ban(user, msg_text):
                                st.error("⛔ Назар аударыңыз! Боқтық сөз қолданғаныңыз үшін жүйе сізді 15 күнге чаттан банға жіберді!")
                                st.rerun()
                            else:
                                chat_messages.append({
                                    "user": user,
                                    "text": msg_text,
                                    "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                                })
                                save_data(st.session_state.app_data)
                                st.rerun()

    elif role == "Student":
        st.title(f"🎓 Оқушы кабинеті: {user}")
        student_direction = users_db[user].get("direction", "Математика - Физика")
        
        # Директор берген атақты шығару
        my_badge = st.session_state.app_data["badges"].get(user, "")
        if my_badge:
            st.success(f"⭐ Сіздің жеке атағыңыз / марапатыңыз: **{my_badge}**")
            
        st.info(f"📌 Сіздің бекітілген бағытыңыз: **{student_direction}**")
        
        tab_s1, tab_s2, tab_s3, tab_s4, tab_s5 = st.tabs(["👤 Профиль & Қатемен жұмыс", "🏆 Рейтинг", "⚔️ Тест & Дуэль", "💬 Чат (Талқылау)", "📬 Хабарландырулар"])
        
        with tab_s1:
            st.subheader("👤 Жеке профиль және қатемен жұмыс")
            results = st.session_state.app_data.get("results", [])
            my_results = [r for r in results if r['student'] == user]
            
            st.write(f"**Логин:** {user} | **Бағыт:** {student_direction}")
            if my_results:
                st.write("### 📝 Тапсырған тесттеріңіз бен нәтижелеріңіз:")
                for mr in my_results:
                    st.write(f"- Пән: **{mr['subject']}** | Ұпай: **{mr['score']} / {mr['total']}** ({mr['date']})")
                
                st.divider()
                st.write("### 🔍 Қатемен жұмыс (Талдау):")
                st.info("Мұнда сіз қай сұрақтардан қате жібергеніңізді көріп, чатта ата-аналармен немесе мұғалімдермен талқылай аласыз.")
            else:
                st.info("Әзірге тест тапсырған жоқсыз.")

        with tab_s2:
            st.subheader("🏆 Жалпы рейтинг")
            results = st.session_state.app_data.get("results", [])
            student_stats = {}
            for r in results:
                s = r['student']
                if s not in student_stats:
                    student_stats[s] = {"score": 0, "total": 0}
                student_stats[s]["score"] += r['score']
                student_stats[s]["total"] += r['total']
            
            ranking_list = sorted([{"student": s, "score": d["score"]} for s, d in student_stats.items()], key=lambda x: x['score'], reverse=True)
            for idx, item in enumerate(ranking_list):
                st.write(f"**{idx+1}-орын:** {item['student']} — Ұпай: {item['score']}")

        with tab_s3:
            st.subheader("🎯 Тест тапсыру")
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
                        with st.form("exam_form"):
                            answers = {}
                            for idx, q in enumerate(qs):
                                st.write(f"**Сұрақ {idx+1}:** {q['text']}")
                                for k, v in q['options'].items():
                                    st.write(f"{k}) {v}")
                                ans = st.multiselect("Жауап", ["A", "B", "C", "D"], key=f"q_{q['id']}")
                                answers[q['id']] = ans
                                st.divider()
                            
                            if st.form_submit_button("Аяқтау"):
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
                st.success("Тест аяқталды!")
                if st.button("Басқа тестке өту"):
                    st.session_state.test_submitted = False
                    st.rerun()

        with tab_s4:
            st.subheader("💬 Ортақ чат және сұрақтарды талқылау")
            bans = st.session_state.app_data.get("bans", {})
            is_banned = False
            if user in bans:
                b_until = datetime.strptime(bans[user], "%Y-%m-%d %H:%M:%S")
                if datetime.now() < b_until:
                    is_banned = True
                    st.error(f"⛔ Боқтық немесе ереже бұзғаныңыз үшін 15 күндік банға түстік! Уақыты: {b_until}")
            
            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}** ({msg['time']}): {msg['text']}")
                
            if not is_banned:
                with st.form("student_chat_form", clear_on_submit=True):
                    msg_text = st.text_input("Хабарлама немесе сұрақ жазыңыз:")
                    if st.form_submit_button("Жіберу"):
                        if msg_text:
                            if check_bad_words_and_ban(user, msg_text):
                                st.error("⛔ Назар аударыңыз! Боқтық сөз қолданғаныңыз үшін жүйе сізді 15 күнге банға жіберді!")
                                st.rerun()
                            else:
                                chat_messages.append({
                                    "user": user,
                                    "text": msg_text,
                                    "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                                })
                                save_data(st.session_state.app_data)
                                st.rerun()

        with tab_s5:
            st.subheader("📬 Хабарландырулар")
            my_notifs = st.session_state.app_data["notifications"].get(user, [])
            for n in reversed(my_notifs):
                st.info(n)
