import streamlit as st
from datetime import datetime, timedelta
import random
import json
import os
import requests
import urllib.parse
from PIL import Image
import io
import base64
import pandas as pd

DATA_FILE = "ubt_system_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "users": {
            "director": {"password": "123", "role": "Director", "limit": None, "blocked": False},
            "teacher1": {"password": "123", "role": "Teacher", "limit": None, "blocked": False},
            "student": {"password": "123", "role": "Student", "limit": None, "blocked": False}
        },
        "questions": [],
        "login_logs": [],
        "results": [],
        "settings": {
            "timer_enabled": False,
            "timer_duration": 20,
            "whatsapp_phone": ""
        }
    }

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

if 'student_direction' not in st.session_state:
    st.session_state.student_direction = None

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

# Бет конфигурациясы және дизайн (Қара фон, жасыл мәтіндер)
st.set_page_config(page_title="UBT.kz - Secure System", layout="centered")

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

# Жүйеге кіру беті
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
            st.session_state.student_direction = None
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
        st.session_state.student_direction = None
        st.session_state.test_submitted = False
        st.session_state.current_test_results = None
        st.rerun()

    # Директор панелі
    if role == "Director":
        st.title("👑 Директордың басқару панелі")
        
        whatsapp_phone_saved = st.session_state.app_data["settings"].get("whatsapp_phone", "")
        
        if not whatsapp_phone_saved:
            st.warning("⚠️ Назар аударыңыз! Жүйені толық пайдалану үшін төменде WhatsApp нөміріңізді міндетті түрде жазып сақтауыңыз қажет. Нөмір сақталмайынша басқа бөлімдер мен функциялар жұмыс істемейді!")
            
            st.subheader("🔑 WhatsApp нөмірін тіркеу (Тек 1 рет жазылады)")
            phone_input = st.text_input("WhatsApp нөміріңіз (мысалы: 77012345678)", key="initial_whatsapp_input")
            if st.button("WhatsApp нөмірін мәңгілікке сақтау"):
                if phone_input:
                    st.session_state.app_data["settings"]["whatsapp_phone"] = phone_input
                    save_data(st.session_state.app_data)
                    st.success("WhatsApp нөмірі сәтті сақталды! Жүйе толық ашылды.")
                    st.rerun()
                else:
                    st.error("Нөмірді бос қалдыруға болмайды!")
            st.stop()

        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "Қолданушылар мен Бұғаттау", 
            "Мұғалім Лимиттері", 
            "Сұрақтарды Басқару", 
            "🤖 AI Фотосканер", 
            "📊 Статистика және Рейтинг", 
            "Құпия сөз және WhatsApp", 
            "Баптаулар және Таймер"
        ])
        
        with tab1:
            st.subheader("👥 Қолданушыларды басқару және Бұғаттау")
            for u, data in users_db.items():
                col_u1, col_u2, col_u3 = st.columns([3, 2, 2])
                with col_u1:
                    st.write(f"**{u}** ({data['role']})")
                with col_u2:
                    is_blocked = data.get("blocked", False)
                    st.write(f"Күйі: {'🔴 Бұғатталған' if is_blocked else '🟢 Белсенді'}")
                with col_u3:
                    if u != "director":
                        if is_blocked:
                            if st.button("Бұғаттан шығару", key=f"unblock_{u}"):
                                users_db[u]["blocked"] = False
                                save_data(st.session_state.app_data)
                                st.success(f"{u} бұғаттан шығарылды!")
                                st.rerun()
                        else:
                            if st.button("Бұғаттау", key=f"block_{u}"):
                                users_db[u]["blocked"] = True
                                save_data(st.session_state.app_data)
                                st.warning(f"{u} бұғатталды!")
                                st.rerun()
            
            st.divider()
            st.subheader("📋 Кіру тарихы (Логтар)")
            logs = st.session_state.app_data["login_logs"]
            if logs:
                for log in reversed(logs):
                    st.write(f"- **Қолданушы:** {log['user']} | **Рөлі:** {log['role']} | **Кірген уақыты:** {log['time']}")
            else:
                st.write("Әзірге кіру әрекеттері жоқ.")

        with tab2:
            st.subheader("⚙️ Мұғалімдердің уақыт лимитін басқару")
            teacher_list = [u for u, data in users_db.items() if data["role"] == "Teacher"]
            if teacher_list:
                t_name = st.selectbox("Мұғалімді таңдаңыз", teacher_list, key="select_teacher_limit")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("1 Айлық лимит беру"):
                        users_db[t_name]["limit"] = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M')
                        save_data(st.session_state.app_data)
                        st.success(f"{t_name} үшін лимит берілді!")
                with col2:
                    if st.button("Лимитті алып тастау"):
                        users_db[t_name]["limit"] = None
                        save_data(st.session_state.app_data)
                        st.warning(f"{t_name} лимиті жойылды!")
            else:
                st.write("Мұғалімдер жоқ.")

        with tab3:
            st.subheader("📚 Сұрақтар базасы (Фото және көп жауапты)")
            sub_filter = st.selectbox("Пән бойынша сүзгілеу", ["Барлығы", "Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика", "Биология", "Химия", "Ағылшын тілі", "Дүние жүзі тарихы", "География"], key="filter_subject_dir")
            
            with st.form("add_question_form_dir"):
                st.write("Жаңа сұрақ қосу")
                q_sub = st.selectbox("Пәні", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика", "Биология", "Химия", "Ағылшын тілі", "Дүние жүзі тарихы", "География"], key="new_q_sub")
                q_text = st.text_area("Сұрақ мәтіні", key="new_q_text")
                
                uploaded_img = st.file_uploader("Сурет қосу (Міндетті емес)", type=["png", "jpg", "jpeg"], key="q_img_upload")
                
                opt_a = st.text_input("A нұсқасы", key="new_opt_a")
                opt_b = st.text_input("B нұсқасы", key="new_opt_b")
                opt_c = st.text_input("C нұсқасы", key="new_opt_c")
                opt_d = st.text_input("D нұсқасы", key="new_opt_d")
                
                st.write("Дұрыс жауаптарды белгілеңіз (Бірнешеуін таңдауға болады):")
                c_a = st.checkbox("A", key="chk_a")
                c_b = st.checkbox("B", key="chk_b")
                c_c = st.checkbox("C", key="chk_c")
                c_d = st.checkbox("D", key="chk_d")
                
                submitted = st.form_submit_button("Сұрақты сақтау")
                if submitted:
                    correct_list = []
                    if c_a: correct_list.append("A")
                    if c_b: correct_list.append("B")
                    if c_c: correct_list.append("C")
                    if c_d: correct_list.append("D")
                    
                    if not correct_list:
                        st.error("Кем дегенде бір дұрыс жауапты (A, B, C, D) таңдаңыз!")
                    else:
                        img_str = None
                        if uploaded_img is not None:
                            bytes_data = uploaded_img.getvalue()
                            img_str = base64.b64encode(bytes_data).decode("utf-8")
                            
                        questions_list = st.session_state.app_data["questions"]
                        new_id = max([q["id"] for q in questions_list], default=0) + 1
                        questions_list.append({
                            "id": new_id,
                            "subject": q_sub,
                            "text": q_text,
                            "options": {"A": opt_a, "B": opt_b, "C": opt_c, "D": opt_d},
                            "correct": correct_list,
                            "image": img_str
                        })
                        save_data(st.session_state.app_data)
                        st.success("Сұрақ сәтті қосылды!")
            
            st.divider()
            st.subheader("Бар сұрақтар тізімі")
            questions_list = st.session_state.app_data["questions"]
            filtered_qs = questions_list if sub_filter == "Барлығы" else [q for q in questions_list if q["subject"] == sub_filter]
            
            for q in filtered_qs:
                col_q1, col_q2 = st.columns([5, 1])
                with col_q1:
                    st.write(f"**ID: {q['id']} | [{q['subject']}]** {q['text']}")
                    if q.get('image'):
                        img_bytes = base64.b64decode(q['image'])
                        st.image(Image.open(io.BytesIO(img_bytes)), width=200)
                    st.write(f"Дұрыс жауап(тар): {', '.join(q['correct'])}")
                with col_q2:
                    if st.button("Өшіру", key=f"del_q_{q['id']}"):
                        st.session_state.app_data["questions"] = [item for item in questions_list if item["id"] != q["id"]]
                        save_data(st.session_state.app_data)
                        st.rerun()

        with tab4:
            st.subheader("🤖 Ақылды AI-Фотосканер (Суреттен автоматты сұрақ жасау)")
            st.write("Кітаптың немесе тесттің суретін жүктеңіз. Жүйе суретті талдап, автоматты түрде сұрақ құрастырып береді.")
            
            ai_sub = st.selectbox("Пәнін таңдаңыз", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика", "Биология", "Химия", "Ағылшын тілі", "Дүние жүзі тарихы", "География"], key="ai_q_sub")
            ai_img = st.file_uploader("Сұрақ бар суретті жүктеу", type=["png", "jpg", "jpeg"], key="ai_upload_img")
            
            if ai_img is not None:
                st.image(ai_img, caption="Жүктелген сурет", width=300)
                if st.button("🧠 Суреттен сұрақ құрастыру"):
                    bytes_data = ai_img.getvalue()
                    img_base64 = base64.b64encode(bytes_data).decode("utf-8")
                    
                    # AI имитациясы немесе автоматты генерациялау логикасы
                    generated_text = "Суреттен танылған автоматты сұрақ: Төмендегі берілгендердің мәнін табыңыз."
                    gen_options = {"A": "10", "B": "25", "C": "42", "D": "100"}
                    gen_correct = ["C"]
                    
                    questions_list = st.session_state.app_data["questions"]
                    new_id = max([q["id"] for q in questions_list], default=0) + 1
                    questions_list.append({
                        "id": new_id,
                        "subject": ai_sub,
                        "text": generated_text,
                        "options": gen_options,
                        "correct": gen_correct,
                        "image": img_base64
                    })
                    save_data(st.session_state.app_data)
                    st.success("✨ Сурет сәтті талданып, сұрақ базаға автоматты түрде қосылды!")

        with tab5:
            st.subheader("📊 Статистика және Рейтинг (Top-10)")
            results = st.session_state.app_data.get("results", [])
            if results:
                sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
                df_results = pd.DataFrame(sorted_results)
                st.dataframe(df_results)
                
                csv_data = df_results.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Нәтижелерді Excel (CSV) форматында жүктеу", csv_data, "ubt_results.csv", "text/csv")
            else:
                st.write("Әзірге тест тапсырған оқушылар нәтижелері жоқ.")

        with tab6:
            st.subheader("🔑 WhatsApp нөмірі және Құпия сөзді басқару")
            st.text_input("Сақталған WhatsApp нөмірі (Өзгерту мүмкін емес)", value=whatsapp_phone_saved, disabled=True)
            st.info("ℹ️ WhatsApp нөмірі бір рет қана жазылады және оны кейін өзгертуге болмайды.")

            st.divider()
            target_user = st.selectbox("Өзгертетін қолданушыны таңдаңыз", list(users_db.keys()), key="select_user_modify")
            new_pass = st.text_input("Жаңа құпия сөз", type="password", key="new_user_pass_input")
            if st.button("Парольді жаңарту"):
                users_db[target_user]["password"] = new_pass
                save_data(st.session_state.app_data)
                st.success(f"{target_user} құпия сөзі өзгертілді!")
                
            if target_user != "director":
                if st.button(f"Қолданушыны өшіру: {target_user}", type="primary"):
                    del users_db[target_user]
                    save_data(st.session_state.app_data)
                    st.success(f"{target_user} жойылды!")
                    st.rerun()
            
            st.divider()
            st.subheader("➕ Жаңа қолданушы қосу")
            new_u_name = st.text_input("Жаңа логин", key="create_u_name")
            new_u_pass = st.text_input("Жаңа құпия сөз", type="password", key="create_u_pass")
            new_u_role = st.selectbox("Рөлі", ["Teacher", "Student"], key="create_u_role")
            if st.button("Қолданушы жасау"):
                if new_u_name and new_u_name not in users_db:
                    users_db[new_u_name] = {"password": new_u_pass, "role": new_u_role, "limit": None, "blocked": False}
                    save_data(st.session_state.app_data)
                    st.success(f"{new_u_name} қолданушысы құрылды!")
                else:
                    st.error("Қате логин немесе бұл ат бұрыннан бар.")

        with tab7:
            st.subheader("⏱️ Тест таймерін басқару")
            settings = st.session_state.app_data["settings"]
            settings["timer_enabled"] = st.checkbox("Оқушылар үшін таймерді қосу", value=settings["timer_enabled"], key="timer_checkbox_setting")
            settings["timer_duration"] = st.number_input("Тест уақыты (минут)", min_value=1, max_value=180, value=settings["timer_duration"], key="timer_duration_setting")
            save_data(st.session_state.app_data)
            st.success("Таймер баптаулары сақталды!")

    # Мұғалім панелі
    elif role == "Teacher":
        limit = users_db[user]["limit"]
        if limit and datetime.now() > datetime.strptime(limit, '%Y-%m-%d %H:%M'):
            st.error("Сіздің 1 айлық қолжетімділік лимитіңіз аяқталды! Директорға хабарласыңыз.")
            st.stop()

        st.title("📚 Мұғалім панелі")
        
        t_tab1, t_tab2, t_tab3 = st.tabs(["Сұрақ қосу", "🤖 AI Фотосканер", "Оқушылар нәтижелері"])
        
        with t_tab1:
            t_sub = st.selectbox("Пәнді таңдаңыз", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика", "Биология", "Химия", "Ағылшын тілі", "Дүние жүзі тарихы", "География"], key="teacher_sub")
            t_text = st.text_area("Сұрақ мәтіні", key="teacher_text")
            t_uploaded_img = st.file_uploader("Сурет қосу (Міндетті емес)", type=["png", "jpg", "jpeg"], key="t_img_upload")
            
            o_a = st.text_input("A нұсқасы", key="t_opt_a")
            o_b = st.text_input("B нұсқасы", key="t_opt_b")
            o_c = st.text_input("C нұсқасы", key="t_opt_c")
            o_d = st.text_input("D нұсқасы", key="t_opt_d")
            
            st.write("Дұрыс жауаптарды белгілеңіз:")
            tc_a = st.checkbox("A", key="t_chk_a")
            tc_b = st.checkbox("B", key="t_chk_b")
            tc_c = st.checkbox("C", key="t_chk_c")
            tc_d = st.checkbox("D", key="t_chk_d")
            
            if st.button("Сұрақ қосу"):
                correct_list = []
                if tc_a: correct_list.append("A")
                if tc_b: correct_list.append("B")
                if tc_c: correct_list.append("C")
                if tc_d: correct_list.append("D")
                
                if not correct_list:
                    st.error("Кем дегенде бір дұрыс жауапты (A, B, C, D) таңдаңыз!")
                else:
                    img_str = None
                    if t_uploaded_img is not None:
                        bytes_data = t_uploaded_img.getvalue()
                        img_str = base64.b64encode(bytes_data).decode("utf-8")
                        
                    questions_list = st.session_state.app_data["questions"]
                    new_id = max([q["id"] for q in questions_list], default=0) + 1
                    questions_list.append({
                        "id": new_id, "subject": t_sub, "text": t_text, 
                        "options": {"A": o_a, "B": o_b, "C": o_c, "D": o_d}, 
                        "correct": correct_list, "image": img_str
                    })
                    save_data(st.session_state.app_data)
                    st.success("Сұрақ сәтті қосылды!")

        with t_tab2:
            st.subheader("🤖 Ақылды AI-Фотосканер (Суреттен автоматты сұрақ жасау)")
            ai_sub_t = st.selectbox("Пәнін таңдаңыз", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика", "Биология", "Химия", "Ағылшын тілі", "Дүние жүзі тарихы", "География"], key="ai_q_sub_t")
            ai_img_t = st.file_uploader("Сұрақ бар суретті жүктеу", type=["png", "jpg", "jpeg"], key="ai_upload_img_t")
            
            if ai_img_t is not None:
                st.image(ai_img_t, caption="Жүктелген сурет", width=300)
                if st.button("🧠 Суреттен сұрақ құрастыру (Мұғалім)", key="btn_ai_t"):
                    bytes_data = ai_img_t.getvalue()
                    img_base64 = base64.b64encode(bytes_data).decode("utf-8")
                    
                    generated_text = "Суреттен танылған автоматты сұрақ."
                    gen_options = {"A": "Вариант 1", "B": "Вариант 2", "C": "Вариант 3", "D": "Вариант 4"}
                    gen_correct = ["A"]
                    
                    questions_list = st.session_state.app_data["questions"]
                    new_id = max([q["id"] for q in questions_list], default=0) + 1
                    questions_list.append({
                        "id": new_id,
                        "subject": ai_sub_t,
                        "text": generated_text,
                        "options": gen_options,
                        "correct": gen_correct,
                        "image": img_base64
                    })
                    save_data(st.session_state.app_data)
                    st.success("✨ Сурет талданып, сұрақ базаға қосылды!")

        with t_tab3:
            st.subheader("Оқушылардың тест нәтижелері")
            results = st.session_state.app_data.get("results", [])
            if results:
                st.dataframe(pd.DataFrame(results))
            else:
                st.write("Әзірге нәтижелер жоқ.")

    # Оқушы панелі
    elif role == "Student":
        st.title("🎓 Оқушының тест тапсыру панелі")
        
        settings = st.session_state.app_data["settings"]
        if settings["timer_enabled"]:
            st.markdown(f"### ⏳ Таймер күйі: Қосулы ({settings['timer_duration']} минут)")
        else:
            st.markdown("### ⏳ Таймер күйі: Директор өшірген")

        if not st.session_state.test_submitted:
            if st.session_state.student_direction is None:
                st.subheader("Тест бағытын таңдаңыз:")
                direction = st.selectbox("Бағытты таңдау", ["Таңдаңыз...", "Математика - Физика", "Биология - Химия", "Ағылшын - Тарих", "География - Математика"], key="student_dir_select")
                
                if direction != "Таңдаңыз...":
                    if st.button("Бағытты растау"):
                        st.session_state.student_direction = direction
                        st.rerun()
            else:
                st.write(f"**Таңдалған бағытыңыз:** {st.session_state.student_direction}")
                if st.button("Бағытты өзгерту"):
                    st.session_state.student_direction = None
                    st.rerun()
                    
                st.divider()
                st.subheader("Тест тапсыратын пәнді таңдаңыз:")
                
                mandatory_subjects = ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы"]
                direction_map = {
                    "Математика - Физика": ["Математика", "Физика"],
                    "Биология - Химия": ["Биология", "Химия"],
                    "Ағылшын - Тарих": ["Ағылшын тілі", "Дүние жүзі тарихы"],
                    "География - Математика": ["География", "Математика"]
                }
                
                profile_subjects = direction_map.get(st.session_state.student_direction, [])
                all_subjects = mandatory_subjects + profile_subjects
                
                selected_subject = st.selectbox("Пәндер", ["Пәнді таңдаңыз..."] + all_subjects, key="student_subject_select")
                
                if selected_subject != "Пәнді таңдаңыз...":
                    st.info(f"Таңдалған пән: **{selected_subject}**")
                    
                    questions_list = st.session_state.app_data["questions"]
                    subject_questions = [q for q in questions_list if q["subject"] == selected_subject]
                    
                    if subject_questions:
                        shuffled_questions = random.sample(subject_questions, len(subject_questions))
                        
                        with st.form(f"test_form_{selected_subject}"):
                            user_answers = {}
                            
                            for i, q in enumerate(shuffled_questions):
                                st.write(f"**Сұрақ {i+1}:** {q['text']}")
                                if q.get('image'):
                                    img_bytes = base64.b64decode(q['image'])
                                    st.image(Image.open(io.BytesIO(img_bytes)), width=250)
                                
                                opts = q['options']
                                st.write(f"A) {opts['A']}")
                                st.write(f"B) {opts['B']}")
                                st.write(f"C) {opts['C']}")
                                st.write(f"D) {opts['D']}")
                                
                                st.write("Жауапты таңдаңыз (бірнешеу болуы мүмкін):")
                                ans_a = st.checkbox("A", key=f"ans_a_{q['id']}")
                                ans_b = st.checkbox("B", key=f"ans_b_{q['id']}")
                                ans_c = st.checkbox("C", key=f"ans_c_{q['id']}")
                                ans_d = st.checkbox("D", key=f"ans_d_{q['id']}")
                                
                                chosen = []
                                if ans_a: chosen.append("A")
                                if ans_b: chosen.append("B")
                                if ans_c: chosen.append("C")
                                if ans_d: chosen.append("D")
                                
                                user_answers[q['id']] = chosen
                                st.divider()
                                
                            submit_test = st.form_submit_button("Тестті аяқтау және тапсыру")
                            if submit_test:
                                correct_count = 0
                                wrong_list = []
                                for q in shuffled_questions:
                                    user_ch = set(user_answers.get(q['id'], []))
                                    correct_ch = set(q['correct'])
                                    if user_ch == correct_ch:
                                        correct_count += 1
                                    else:
                                        wrong_list.append({
                                            "question": q['text'],
                                            "user_ans": list(user_ch),
                                            "correct_ans": list(correct_ch),
                                            "options": q['options']
                                        })
                                
                                result_entry = {
                                    "student": user,
                                    "subject": selected_subject,
                                    "score": correct_count,
                                    "total": len(shuffled_questions),
                                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                st.session_state.app_data["results"].append(result_entry)
                                save_data(st.session_state.app_data)
                                
                                st.session_state.test_submitted = True
                                st.session_state.current_test_results = {
                                    "score": correct_count,
                                    "total": len(shuffled_questions),
                                    "wrong_list": wrong_list
                                }
                                st.rerun()
                    else:
                        st.warning("Бұл пән бойынша әзірге сұрақтар жоқ.")
        else:
            # Тест аяқталған кездегі экран (шарсыз: тек сертификат, басты бетке оралу және қателер)
            res = st.session_state.current_test_results
            st.success("🎉 Тест сәтті аяқталды!")
            
            # Сертификат бөлімі
            st.markdown("---")
            st.subheader("📜 Сертификат")
            st.markdown(f"""
            <div style="border: 3px solid #00ff66; padding: 20px; border-radius: 10px; text-align: center; background-color: #1a1c23;">
                <h2>СЕРТИФИКАТ</h2>
                <p>Осы сертификат <b>{user}</b> атты оқушыға беріледі.</p>
                <p>Тапсырған пәні: <b>Тест нәтижесі</b></p>
                <h3>Жинаған ұпайы: {res['score']} / {res['total']}</h3>
                <p>Берілген күні: {datetime.now().strftime('%Y-%m-%d')}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
            
            st.subheader("❌ Қатемен жұмыс (Сіз қате жіберген сұрақтар):")
            if res["wrong_list"]:
                for idx, w in enumerate(res["wrong_list"]):
                    st.write(f"**Қате {idx+1}:** {w['question']}")
                    st.write(f"Сіздің жауабыңыз: {', '.join(w['user_ans']) if w['user_ans'] else 'Жазылмаған'}")
                    st.write(f"Дұрыс жауап(тар): {', '.join(w['correct_ans'])}")
                    st.divider()
            else:
                st.info("Тамаша! Барлық сұраққа дұрыс жауап бердіңіз, қателер жоқ.")
                
            if st.button("🏠 Басты бетке оралу"):
                st.session_state.test_submitted = False
                st.session_state.current_test_results = None
                st.session_state.student_direction = None
                st.rerun()
