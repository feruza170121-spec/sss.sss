s_msg = st.text_input("Хабарлама жазыңыз:", key="student_chat_message")

if st.button("Жіберу", key="student_chat_send_button"):
    s_msg_str = str(s_msg) if s_msg is not None else ""

    if s_msg_str.strip():
        is_banned = check_bad_words_and_ban(user, s_msg_str)

        if is_banned:
            st.error(
                "⛔ Сіздің хабарламаңыздан тыйым салынған сөздер табылды! "
                "Жүйе ережесі бойынша чаттағы аккаунтыңыз 15 күнге бұғатталды."
            )
        else:
            chat_messages.append({
                "user": f"{user} (Оқушы)",
                "text": s_msg_str,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

            save_data(st.session_state.app_data)
            st.session_state.student_chat_message = ""
            st.rerun()
    else:
        st.error("Хабарлама бос болмауы тиіс.")
