with tab_s4:
            st.subheader("💬 Ортақ чат")
            
            # Бан тексерісі
            now_dt = datetime.now()
            bans_db = st.session_state.app_data.get("bans", {})
            if user in bans_db:
                b_expire = datetime.strptime(bans_db[user], "%Y-%m-%d %H:%M:%S")
                if now_dt < b_expire:
                    st.error(f"⛔ Сіздің чатта жазуыңызға тыйым салынған! Банның аяқталу уақыты: {b_expire.strftime('%Y-%m-%d %H:%M')}")
                else:
                    del st.session_state.app_data["bans"][user]
                    save_data(st.session_state.app_data)

            chat_messages = st.session_state.app_data.get("chat_messages", [])
            for msg in chat_messages:
                st.write(f"💬 **{msg['user']}** ({msg['time']}): {msg['text']}")
                
            with st.form("student_chat_form", clear_on_submit=True):
                s_msg = st.text_input("Хабарлама жазу:")
                if st.form_submit_button("Жіберу"):
                    if s_msg.strip():
                        # Нашар сөздерді тексеру
                        if check_bad_words_and_ban(user, s_msg):
                            st.error("⛔ Әдепсіз сөздер үшін чатта 15 күнге бұғатталдыңыз!")
                        else:
                            chat_messages.append({
                                "user": f"{user} (Оқушы)",
                                "text": s_msg,
                                "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            save_data(st.session_state.app_data)
                            st.rerun()

        with tab_s5:
            st.subheader("📝 Директорға немесе мұғалімдерге заява жіберу")
            with st.form("application_form", clear_on_submit=True):
                app_text = st.text_area("Заява мәтіні (арыз немесе өтініш):")
                if st.form_submit_button("Заяваны жіберу"):
                    if app_text.strip():
                        if "applications" not in st.session_state.app_data:
                            st.session_state.app_data["applications"] = []
                        st.session_state.app_data["applications"].append({
                            "student": user,
                            "text": app_text,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        save_data(st.session_state.app_data)
                        st.success("Заяваңыз сәтті жіберілді!")

        with tab_s6:
            st.subheader("⚖️ Менің жіберген аппеляцияларыım")
            appeals = st.session_state.app_data.get("appeals", [])
            my_appeals = [ap for ap in appeals if ap['student'] == user]
            if my_appeals:
                for ap in my_appeals:
                    st.write(f"📚 **Пән:** {ap['subject']} | 🕒 **Уақыты:** {ap['time']}")
                    st.markdown(f"> **Шағымыңыз:** {ap['text']}")
                    st.divider()
            else:
                st.info("Сіз әзірге аппеляция жіберген жоқсыз.")

        with tab_s7:
            st.subheader("📬 Хабарландырулар")
            notifications = st.session_state.app_data.get("notifications", {})
            user_notifs = notifications.get(user, [])
            if user_notifs:
                for n in user_notifs:
                    st.info(n)
            else:
                st.info("Жаңа хабарландырулар жоқ.")
