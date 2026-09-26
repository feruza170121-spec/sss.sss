import streamlit as st
from datetime import datetime, timedelta
import random
import json
import os
import requests
import urllib.parse

DATA_FILE = "ubt_system_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "users": {
            "director": {"password": "123", "role": "Director", "limit": None},
            "teacher1": {"password": "123", "role": "Teacher", "limit": None},
            "student": {"password": "123", "role": "Student", "limit": None}
        },
        "questions": [
            {"id": 1, "subject": "Математикалық сауаттылық", "text": "2 + 2 нешеге тең?", "options": ["3", "4", "5", "6"], "correct": "4"},
            {"id": 2, "subject": "Физика", "text": "Күштің өлшем бірлігі қандай?", "options": ["Джоуль", "Ньютон", "Ватт", "Паскаль"], "correct": "Ньютон"}
        ],
        "login_logs": [],
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

# Жүйеге кіру беті (Логин мен пароль жазатын жер ағылшынша)
if not st.session_state.logged_in:
    st.title("🔐 UBT.kz Secure Login")
    
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login"):
        now = datetime.now()
        users_db = st.session_state.app_data["users"]
        
        # 30 минуттық блок тексерісі
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
    role = users_db[user]["role"]
    
    st.sidebar.title(f"Қош келдіңіз, {user}!")
    st.sidebar.text(f"Рөлі: {role}")
    
    if st.sidebar.button("Жүйеден шығу"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.student_direction = None
        st.rerun()

    # Директор панелі
    if role == "Director":
        st.title("👑 Директордың басқару панелі")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Қолданушылар мен Логтар", "Мұғалім Лимиттері", "Сұрақтарды Басқару", "Құпия сөз және WhatsApp", "Баптаулар және Таймер"])
        
        with tab1:
            st.subheader("📋 Кіру тарихы (Логтар)")
            logs = st.session_state.app_data["login_logs"]
            if logs:
                for log in reversed(logs):
                    st.write(f"- **Қолданушы:** {log['user']} | **Рөлі:** {log['role']} | **Кірген уақыты:** {log['time']}")
            else:
                st.write("Әзірге кіру әрекеттері жоқ.")
                
            st.subheader("👥 Барлық қолданушылар")
            for u, data in users_db.items():
                st.write(f"- **Қолданушы:** {u} | **Рөлі:** {data['role']} | **Лимиті:** {data['limit']}")

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
            st.subheader("📚 Сұрақтар базасы")
            sub_filter = st.selectbox("Пән бойынша сүзгілеу", ["Барлығы", "Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика", "Биология", "Химия", "Ағылшын тілі", "Дүние жүзі тарихы", "География"], key="filter_subject_dir")
            
            with st.form("add_question_form_dir"):
                st.write("Жаңа сұрақ қосу")
                q_sub = st.selectbox("Пәні", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика", "Биология", "Химия", "Ағылшын тілі", "Дүние жүзі тарихы", "География"], key="new_q_sub")
                q_text = st.text_area("Сұрақ мәтіні", key="new_q_text")
                opt1 = st.text_input("1-ші жауап", key="new_opt1")
                opt2 = st.text_input("2-ші жауап", key="new_opt2")
                opt3 = st.text_input("3-ші жауап", key="new_opt3")
                opt4 = st.text_input("4-ші жауап", key="new_opt4")
                correct = st.text_input("Дұрыс жауап (дәл жазылуы тиіс)", key="new_correct")
                
                submitted = st.form_submit_button("Сұрақты сақтау")
                if submitted:
                    questions_list = st.session_state.app_data["questions"]
                    new_id = max([q["id"] for q in questions_list], default=0) + 1
                    questions_list.append({
                        "id": new_id,
                        "subject": q_sub,
                        "text": q_text,
                        "options": [opt1, opt2, opt3, opt4],
                        "correct": correct
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
                with col_q2:
                    if st.button("Өшіру", key=f"del_q_{q['id']}"):
                        st.session_state.app_data["questions"] = [item for item in questions_list if item["id"] != q["id"]]
                        save_data(st.session_state.app_data)
                        st.rerun()

        with tab4:
            st.subheader("🔑 Құпия сөз және WhatsApp хабарлама баптауы")
            
            current_phone = st.session_state.app_data["settings"].get("whatsapp_phone", "")
            phone_input = st.text_input("WhatsApp нөміріңіз (мысалы: 77012345678)", value=current_phone, key="whatsapp_input_setting")
            if st.button("WhatsApp нөмірін сақтау"):
                st.session_state.app_data["settings"]["whatsapp_phone"] = phone_input
                save_data(st.session_state.app_data)
                st.success("WhatsApp нөмірі сәтті сақталды!")

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
                    users_db[new_u_name] = {"password": new_u_pass, "role": new_u_role, "limit": None}
                    save_data(st.session_state.app_data)
                    st.success(f"{new_u_name} қолданушысы құрылды!")
                else:
                    st.error("Қате логин немесе бұл ат бұрыннан бар.")

        with tab5:
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
        st.write("Мұнда сұрақтар қосып, басқара аласыз.")
        
        t_sub = st.selectbox("Пәнді таңдаңыз", ["Математикалық сауаттылық", "Оқу сауаттылығы", "Қазақстан тарихы", "Математика", "Физика", "Биология", "Химия", "Ағылшын тілі", "Дүние жүзі тарихы", "География"], key="teacher_sub")
        t_text = st.text_area("Сұрақ мәтіні", key="teacher_text")
        o1 = st.text_input("1-ші жауап", key="t_opt1")
        o2 = st.text_input("2-ші жауап", key="t_opt2")
        o3 = st.text_input("3-ші жауап", key="t_opt3")
        o4 = st.text_input("4-ші жауап", key="t_opt4")
        ans = st.text_input("Дұрыс жауап", key="t_ans")
        
        if st.button("Сұрақ қосу"):
            questions_list = st.session_state.app_data["questions"]
            new_id = max([q["id"] for q in questions_list], default=0) + 1
            questions_list.append({
                "id": new_id, "subject": t_sub, "text": t_text, "options": [o1, o2, o3, o4], "correct": ans
            })
            save_data(st.session_state.app_data)
            st.success("Сұрақ сәтті қосылды!")

    # Оқушы панелі
    elif role == "Student":
        st.title("🎓 Оқушының тест тапсыру панелі")
        
        settings = st.session_state.app_data["settings"]
        if settings["timer_enabled"]:
            st.markdown(f"### ⏳ Таймер күйі: Қосулы ({settings['timer_duration']} минут)")
        else:
            st.markdown("### ⏳ Таймер күйі: Директор өшірген")

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
                            
                            shuffled_options = q['options'].copy()
                            random.shuffle(shuffled_options)
                            
                            user_answers[q['id']] = st.radio(f"Жауапты таңдаңыз (Сұрақ {i+1})", shuffled_options, key=f"q_radio_{q['id']}")
                            st.divider()
                            
                        submit_test = st.form_submit_button("Тестті аяқтау және тапсыру")
                        if submit_test:
                            correct_count = 0
                            for q in shuffled_questions:
                                if user_answers.get(q['id']) == q['correct']:
                                    correct_count += 1
                            st.success(f"Тест аяқталды! Сіздің жинаған балыңыз: {correct_count} / {len(shuffled_questions)}")
                else:
                    st.warning("Бұл пән бойынша әзірге сұрақтар жоқ.")
