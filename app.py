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
            {"id": 1, "subject": "Mathematics", "text": "What is 2 + 2?", "options": ["3", "4", "5", "6"], "correct": "4", "image": None},
            {"id": 2, "subject": "Physics", "text": "What is the unit of force?", "options": ["Joule", "Newton", "Watt", "Pascal"], "correct": "Newton", "image": None}
        ],
        "login_logs": [],
        "settings": {
            "timer_enabled": False,
            "timer_duration": 20,
            "whatsapp_phone": ""
        }
    }

def save_data(data):
    # Streamlit file uploader objects cannot be serialized directly to JSON, so we handle images safely
    # For simplicity in file storage, we save text-based question data
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
        # CallMeBot немесе басқа ашық API арқылы WhatsApp-қа хабарлама жіберу логикасы
        encoded_message = urllib.parse.quote(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_message}&apikey=free"
        requests.get(url, timeout=3)
    except Exception:
        pass

# Бет конфигурациясы және дизайн
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
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        now = datetime.now()
        users_db = st.session_state.app_data["users"]
        
        if username in st.session_state.blocked_users:
            unblock_time = st.session_state.blocked_users[username]
            if now < unblock_time:
                remaining = int((unblock_time - now).total_seconds() / 60)
                st.error(f"Account is blocked due to 10 failed attempts. Try again in {remaining} minutes.")
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
            
            # Логқа жазу
            st.session_state.app_data["login_logs"].append({
                "user": username,
                "role": role,
                "time": time_str
            })
            save_data(st.session_state.app_data)
            
            # Егер директор кірсе, WhatsApp-қа хабарлама жіберу
            if role == "Director":
                ph = st.session_state.app_data["settings"].get("whatsapp_phone", "")
                if ph:
                    msg = f"Alert: Director ({username}) logged into the system at {time_str}!"
                    send_whatsapp_alert(ph, msg)
            
            st.rerun()
        else:
            if username not in st.session_state.login_attempts:
                st.session_state.login_attempts[username] = 0
            st.session_state.login_attempts[username] += 1
            
            attempts_left = 10 - st.session_state.login_attempts[username]
            
            if st.session_state.login_attempts[username] >= 10:
                st.session_state.blocked_users[username] = now + timedelta(minutes=30)
                st.error("Password entered incorrectly 10 times! Account is blocked for 30 minutes.")
            else:
                st.error(f"Invalid credentials! Attempts left: {attempts_left}")

else:
    user = st.session_state.current_user
    users_db = st.session_state.app_data["users"]
    role = users_db[user]["role"]
    
    st.sidebar.title(f"Welcome, {user}!")
    st.sidebar.text(f"Role: {role}")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.student_direction = None
        st.rerun()

    # Директор панелі
    if role == "Director":
        st.title("👑 Director Full Access Panel")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Users & Logs", "Teacher Limits", "Manage Questions", "Credentials & WhatsApp", "Settings & Timer"])
        
        with tab1:
            st.subheader("📋 Login Logs")
            logs = st.session_state.app_data["login_logs"]
            if logs:
                for log in reversed(logs):
                    st.write(f"- **User:** {log['user']} | **Role:** {log['role']} | **Time:** {log['time']}")
            else:
                st.write("No login activity yet.")
                
            st.subheader("👥 All System Users")
            for u, data in users_db.items():
                st.write(f"- **User:** {u} | **Role:** {data['role']} | **Limit:** {data['limit']}")

        with tab2:
            st.subheader("⚙️ Teacher Limit Management")
            teacher_list = [u for u, data in users_db.items() if data["role"] == "Teacher"]
            if teacher_list:
                t_name = st.selectbox("Select Teacher", teacher_list)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Grant 1-Month Limit"):
                        users_db[t_name]["limit"] = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M')
                        save_data(st.session_state.app_data)
                        st.success(f"Granted to {t_name}!")
                with col2:
                    if st.button("Revoke Limit"):
                        users_db[t_name]["limit"] = None
                        save_data(st.session_state.app_data)
                        st.warning(f"Revoked for {t_name}!")
            else:
                st.write("No teachers available.")

        with tab3:
            st.subheader("📚 Question Bank Management")
            sub_filter = st.selectbox("Filter by Subject", ["All", "Mathematical Literacy", "Reading Literacy", "History of Kazakhstan", "Mathematics", "Physics", "Biology", "Chemistry", "English", "World History", "Geography"])
            
            with st.form("add_question_form"):
                st.write("Add New Question")
                q_sub = st.selectbox("Subject", ["Mathematical Literacy", "Reading Literacy", "History of Kazakhstan", "Mathematics", "Physics", "Biology", "Chemistry", "English", "World History", "Geography"])
                q_text = st.text_area("Question Text")
                q_img = st.file_uploader("Upload Image (Optional)", type=["png", "jpg", "jpeg"])
                opt1 = st.text_input("Option 1")
                opt2 = st.text_input("Option 2")
                opt3 = st.text_input("Option 3")
                opt4 = st.text_input("Option 4")
                correct = st.text_input("Correct Answer (Exact match)")
                
                submitted = st.form_submit_button("Save Question")
                if submitted:
                    questions_list = st.session_state.app_data["questions"]
                    new_id = max([q["id"] for q in questions_list], default=0) + 1
                    questions_list.append({
                        "id": new_id,
                        "subject": q_sub,
                        "text": q_text,
                        "options": [opt1, opt2, opt3, opt4],
                        "correct": correct,
                        "image": None # File object handled or omitted in JSON
                    })
                    save_data(st.session_state.app_data)
                    st.success("Question added successfully!")
            
            st.divider()
            st.subheader("Existing Questions List")
            questions_list = st.session_state.app_data["questions"]
            filtered_qs = questions_list if sub_filter == "All" else [q for q in questions_list if q["subject"] == sub_filter]
            
            for q in filtered_qs:
                col_q1, col_q2, col_q3 = st.columns([4, 1, 1])
                with col_q1:
                    st.write(f"**ID: {q['id']} | [{q['subject']}]** {q['text']}")
                with col_q2:
                    if st.button("Edit", key=f"edit_{q['id']}"):
                        st.info(f"Editing question ID {q['id']}")
                with col_q3:
                    if st.button("Delete", key=f"del_{q['id']}"):
                        st.session_state.app_data["questions"] = [item for item in questions_list if item["id"] != q["id"]]
                        save_data(st.session_state.app_data)
                        st.rerun()

        with tab4:
            st.subheader("🔑 Credentials & WhatsApp Alert Setup")
            
            # WhatsApp phone number configuration (entered once)
            current_phone = st.session_state.app_data["settings"].get("whatsapp_phone", "")
            phone_input = st.text_input("Your WhatsApp Phone Number (with country code, e.g. 77012345678)", value=current_phone)
            if st.button("Save WhatsApp Number (Once)"):
                st.session_state.app_data["settings"]["whatsapp_phone"] = phone_input
                save_data(st.session_state.app_data)
                st.success("WhatsApp number successfully saved!")

            st.divider()
            target_user = st.selectbox("Select User to Modify/Delete", list(users_db.keys()))
            new_pass = st.text_input("New Password", type="password")
            if st.button("Update Password"):
                users_db[target_user]["password"] = new_pass
                save_data(st.session_state.app_data)
                st.success(f"Password updated for {target_user}!")
                
            if target_user != "director":
                if st.button(f"Delete User: {target_user}", type="primary"):
                    del users_db[target_user]
                    save_data(st.session_state.app_data)
                    st.success(f"User {target_user} deleted!")
                    st.rerun()
            
            st.divider()
            st.subheader("➕ Create New User")
            new_u_name = st.text_input("New Username")
            new_u_pass = st.text_input("New User Password", type="password")
            new_u_role = st.selectbox("Role", ["Teacher", "Student"])
            if st.button("Create User"):
                if new_u_name and new_u_name not in users_db:
                    users_db[new_u_name] = {"password": new_u_pass, "role": new_u_role, "limit": None}
                    save_data(st.session_state.app_data)
                    st.success(f"User {new_u_name} created!")
                else:
                    st.error("Invalid username or already exists.")

        with tab5:
            st.subheader("⏱️ Test Timer Control")
            settings = st.session_state.app_data["settings"]
            settings["timer_enabled"] = st.checkbox("Enable Global Test Timer for Students", value=settings["timer_enabled"])
            settings["timer_duration"] = st.number_input("Test Duration (Minutes)", min_value=1, max_value=180, value=settings["timer_duration"])
            save_data(st.session_state.app_data)
            st.success("Timer settings updated!")

    # Мұғалім панелі
    elif role == "Teacher":
        limit = users_db[user]["limit"]
        if limit and datetime.now() > datetime.strptime(limit, '%Y-%m-%d %H:%M'):
            st.error("Your 1-month access limit has expired! Please contact the Director.")
            st.stop()

        st.title("📚 Teacher Panel")
        st.write("Here you can manage and view questions.")
        
        t_sub = st.selectbox("Select Subject", ["Mathematical Literacy", "Reading Literacy", "History of Kazakhstan", "Mathematics", "Physics", "Biology", "Chemistry", "English", "World History", "Geography"])
        t_text = st.text_area("Question Text")
        o1 = st.text_input("Option 1")
        o2 = st.text_input("Option 2")
        o3 = st.text_input("Option 3")
        o4 = st.text_input("Option 4")
        ans = st.text_input("Correct Answer")
        
        if st.button("Add Question"):
            questions_list = st.session_state.app_data["questions"]
            new_id = max([q["id"] for q in questions_list], default=0) + 1
            questions_list.append({
                "id": new_id, "subject": t_sub, "text": t_text, "options": [o1, o2, o3, o4], "correct": ans, "image": None
            })
            save_data(st.session_state.app_data)
            st.success("Question added successfully!")

    # Оқушы панелі
    elif role == "Student":
        st.title("🎓 Student Testing Panel")
        
        settings = st.session_state.app_data["settings"]
        if settings["timer_enabled"]:
            st.markdown(f"### ⏳ Timer Status: Enabled ({settings['timer_duration']} Minutes)")
        else:
            st.markdown("### ⏳ Timer Status: Disabled by Director")

        if st.session_state.student_direction is None:
            st.subheader("Select your exam profile direction:")
            direction = st.selectbox("Choose direction", ["Select...", "Math - Physics", "Biology - Chemistry", "English - History", "Geography - Math"])
            
            if direction != "Select...":
                if st.button("Confirm Direction"):
                    st.session_state.student_direction = direction
                    st.rerun()
        else:
            st.write(f"**Your selected direction:** {st.session_state.student_direction}")
            if st.button("Change Direction"):
                st.session_state.student_direction = None
                st.rerun()
                
            st.divider()
            st.subheader("Choose a subject to take tests separately:")
            
            mandatory_subjects = ["Mathematical Literacy", "Reading Literacy", "History of Kazakhstan"]
            direction_map = {
                "Math - Physics": ["Mathematics", "Physics"],
                "Biology - Chemistry": ["Biology", "Chemistry"],
                "English - History": ["English", "World History"],
                "Geography - Math": ["Geography", "Mathematics"]
            }
            
            profile_subjects = direction_map.get(st.session_state.student_direction, [])
            all_subjects = mandatory_subjects + profile_subjects
            
            selected_subject = st.selectbox("Subjects", ["Select subject..."] + all_subjects)
            
            if selected_subject != "Select subject...":
                st.info(f"Taking test for: **{selected_subject}**")
                
                questions_list = st.session_state.app_data["questions"]
                subject_questions = [q for q in questions_list if q["subject"] == selected_subject]
                
                if subject_questions:
                    shuffled_questions = random.sample(subject_questions, len(subject_questions))
                    
                    with st.form(f"test_form_{selected_subject}"):
                        user_answers = {}
                        
                        for i, q in enumerate(shuffled_questions):
                            st.write(f"**Question {i+1}:** {q['text']}")
                            
                            shuffled_options = q['options'].copy()
                            random.shuffle(shuffled_options)
                            
                            user_answers[q['id']] = st.radio(f"Select answer for Q{i+1}", shuffled_options, key=f"q_{q['id']}")
                            st.divider()
                            
                        submit_test = st.form_submit_button("Submit Test")
                        if submit_test:
                            correct_count = 0
                            for q in shuffled_questions:
                                if user_answers.get(q['id']) == q['correct']:
                                    correct_count += 1
                            st.success(f"Test submitted! Your score: {correct_count} / {len(shuffled_questions)}")
                else:
                    st.warning("No questions available for this subject yet.")
