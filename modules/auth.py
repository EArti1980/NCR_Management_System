import streamlit as st
import pandas as pd
import os
import random
import string
from modules.core import send_email, log_audit

def show_auth_page():
    """Полный цикл авторизации, регистрации и восстановления пароля"""
    st.title("🔐 Система управления НС - Вход")
    mode = st.radio("Выберите действие:", ["Вход", "Регистрация", "Забыли пароль?"])

    if mode == "Регистрация":
        with st.form("reg_form"):
            fio = st.text_input("ФИО полностью")
            email = st.text_input("Корпоративный Email")
            u_role = st.selectbox("Ваша роль", ["Сотрудник", "QA Менеджер", "Admin"])
            if st.form_submit_button("Запросить доступ"):
                if fio and email:
                    users = pd.read_csv('users.csv') if os.path.exists('users.csv') else pd.DataFrame(columns=['name','email','password','role'])
                    if email in users['email'].values:
                        st.error("Пользователь с таким email уже существует")
                    else:
                        temp_pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                        if send_email(email, "Доступ к системе НС", f"Ваш пароль для входа: {temp_pwd}"):
                            new_u = pd.DataFrame([[fio, email, temp_pwd, u_role]], columns=['name','email','password','role'])
                            new_u.to_csv('users.csv', mode='a', header=not os.path.exists('users.csv'), index=False)
                            st.success(f"✅ Пароль отправлен на {email}")
                            log_audit("Система", "Регистрация", email)

    elif mode == "Забыли пароль?":
        with st.form("forgot"):
            email_res = st.text_input("Введите Email для восстановления")
            if st.form_submit_button("Выслать пароль"):
                if os.path.exists('users.csv'):
                    users = pd.read_csv('users.csv')
                    u_data = users[users['email'] == email_res]
                    if not u_data.empty:
                        # Используем [0] перед ['password'], чтобы избежать ошибок обращения
                        send_email(email_res, "Восстановление доступа", f"Ваш пароль: {u_data.iloc[0]['password']}")
                        st.success("Инструкции отправлены на почту.")
                    else: st.error("Email не найден в базе")

    else:
        with st.form("login_form"):
            le = st.text_input("Email")
            lp = st.text_input("Пароль", type="password")
            if st.form_submit_button("Войти в систему"):
                if os.path.exists('users.csv'):
                    users = pd.read_csv('users.csv')
                    valid = users[(users['email'] == le) & (users['password'] == lp)]
                    if not valid.empty:
                        user_info = valid.iloc[0]
                        st.session_state.update({
                            'auth': True,
                            'u_name': user_info['name'],
                            'u_role': user_info['role'],
                            'active_role': user_info['role']
                        })
                        log_audit(st.session_state['u_name'], "Вход", "Успешно")
                        st.rerun()
                    else: st.error("Неверный логин или пароль")
