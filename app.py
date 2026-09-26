import streamlit as st
from datetime import datetime, timedelta

# Бет конфигурациясы
st.set_page_config(page_title="UBT.kz - Мектеп жүйесі", layout="centered")

# Сессияны басқару (қолданушылар мен блоктауларды сақтау)
if 'users' not in st.session_state:
    st.session_state.users = {
        "директор": {"password": "123", "role": "Директор", "limit": None},
        "мугалим": {"password": "123", "role": "Мұғалім", "limit": None},
        "окушы": {"password": "123", "role": "Оқушы", "limit": None}
    }

if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = {}

if 'blocked_users' not in st.session_state:
    st.session_state.blocked_users = {}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

# Басты бет немесе жүйеге кіру
if not st.session_state.logged_in:
    st.title("🔐 UBT.kz Жүйесіне Кіру")
    
    username = st.text_input("Логин (директор / мугалим / окушы)")
    password = st.text_input("Құпия сөз", type="password")
    
    if st.button("Кіру"):
        now = datetime.now()
        
        # Блоктауды тексеру
        if username in st.session_state.blocked_users:
            unblock_time = st.session_state.blocked_users[username]
            if now < unblock_time:
                remaining = int((unblock_time - now).total_seconds() / 60)
                st.error(f"Бұл аккаунт қате парольдер санынан кейін бұғатталған. {remaining} минуттан кейін көріңіз.")
                st.stop()
            else:
                del st.session_state.blocked_users[username]
                st.session_state.login_attempts[username] = 0

        # Логин мен парольді тексеру
        if username in st.session_state.users and st.session_state.users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.current_user = username
            st.session_state.login_attempts[username] = 0
            st.rerun()
        else:
            # Қате попыткаларды санау
            if username not in st.session_state.login_attempts:
                st.session_state.login_attempts[username] = 0
            st.session_state.login_attempts[username] += 1
            
            attempts_left = 10 - st.session_state.login_attempts[username]
            
            if st.session_state.login_attempts[username] >= 10:
                st.session_state.blocked_users[username] = now + timedelta(minutes=30)
                st.error("Құпия сөз 10 рет қате енгізілді! Аккаунт 30 минутқа бұғатталды.")
            else:
                st.error(f"Қате логин немесе құпия сөз! Қалған әрекет саны: {attempts_left}")

else:
    user = st.session_state.current_user
    role = st.session_state.users[user]["role"]
    
    st.sidebar.title(f"Қош келдіңіз, {user}!")
    st.sidebar.text(f"Рөлі: {role}")
    
    if st.sidebar.button("Шығу"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.rerun()

    # Мұғалімнің лимитін тексеру
    if role == "Мұғалім":
        limit = st.session_state.users[user]["limit"]
        if limit and datetime.now() > limit:
            st.error("Сіздің 1 айлық қолжетімділік лимитіңіз аяқталды! Директорға хабарласыңыз.")
            st.stop()
        elif limit:
            st.info(f"Лимит аяқталатын уақыты: {limit.strftime('%Y-%m-%d %H:%M')}")

    # Интерфейс бөліктері
    if role == "Директор":
        st.title("👑 Директор панелі")
        st.write("Мұғалімдерге 1 айлық лимит беру немесе басқару:")
        
        teacher_name = st.selectbox("Мұғалімді таңдаңыз", [u for u, data in st.session_state.users.items() if data["role"] == "Мұғалім"])
        
        if st.button("1 айлық лимит беру"):
            st.session_state.users[teacher_name]["limit"] = datetime.now() + timedelta(days=30)
            st.success(f"{teacher_name} үшін 1 айлық лимит сәтті берілді!")

    elif role == "Мұғалім":
        st.title("📚 Мұғалім панелі")
        st.write("Мұнда оқу материалдары мен тесттерді басқара аласыз.")

    elif role == "Оқушы":
        st.title("🎓 Оқушы панелі")
        st.write("ҰБТ-ға дайындық тесттері мен тапсырмалар.")
