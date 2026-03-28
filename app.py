import streamlit as st
import pandas as pd
import os
from config import PROCESSES
# Импортируем функции из наших новых модулей
from modules.auth import show_auth_page
from modules.analytics import get_nc_analytics
from modules.ui_employee import show_employee_interface
from modules.ui_qa import show_qa_interface

# --- 1. ИНИЦИАЛИЗАЦИЯ И НАСТРОЙКИ ---
st.set_page_config(page_title="Система управления НС", layout="wide", page_icon="🛡️")

# Имя файла базы данных (Убедитесь, что оно в .gitignore!)
DB_FILE = 'nc_main_data.csv'

# РАСШИРЕННЫЙ СПИСОК КОЛОНОК (согласно архитектуре проекта)
DB_COLS = [
    'ID', 'Дата_Время', 'Автор', 'Код', 'Процесс', 'Описание_OPS', 'Описание_QA', 
    'Кол_во', 'Источник', 'Категория', 'Статус',
    'Correction', 'Corr_Deadline', 'Corr_Owner', 'Corr_Done', # Блок Коррекции
    'Root_Cause', 'CAPA_Plan', 'CAPA_Deadline', 'CAPA_Owner', 'CAPA_Done', # Блок CAPA
    'QA_Comment', 'Is_Recurrent' # Контроль эффективности и повторности
]

# Проверка наличия базы при старте
if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=DB_COLS).to_csv(DB_FILE, index=False)

# Инициализация состояния сессии
if 'auth' not in st.session_state:
    st.session_state['auth'] = False
if 'active_role' not in st.session_state:
    st.session_state['active_role'] = None

# --- 2. ПРОВЕРКА АВТОРИЗАЦИИ ---
if not st.session_state['auth']:
    show_auth_page()
    st.stop() 

# Если роль еще не выбрана (для не-админов), присваиваем её из профиля
if st.session_state['active_role'] is None:
    st.session_state['active_role'] = st.session_state['u_role']

# --- 3. БОКОВАЯ ПАНЕЛЬ (SIDEBAR) ---
st.sidebar.success(f"👤 {st.session_state['u_name']} ({st.session_state['u_role']})")

# Логика переключения ролей для Админа
if st.session_state['u_role'] == "Admin":
    st.sidebar.warning("🛠️ АДМИН-ПАНЕЛЬ")
    st.session_state['active_role'] = st.sidebar.radio(
        "Переключить интерфейс на:", 
        ["Сотрудник", "QA Менеджер"],
        index=0 if st.session_state['active_role'] == "Сотрудник" else 1
    )

st.sidebar.markdown("---")

# Блок графиков EWMA
if st.sidebar.checkbox("📊 Показать графики трендов"):
    p_an = st.sidebar.selectbox("Выберите процесс:", list(PROCESSES.keys()))
    
    for c_type in ["IntMinor", "ExtMinor"]:
        data_plot = get_nc_analytics(p_an, c_type)
        if data_plot is not None and not data_plot.empty:
            # Проверяем наличие колонки Alert перед выводом
            is_alert = data_plot.iloc[-1].get('Alert', False)
            st.sidebar.write(f"{'🔴 ALERT' if is_alert else '📈'} **{c_type}**")
            st.sidebar.line_chart(data_plot, x='Дата_Время', y=['EWMA', 'UCL'])
        else:
            st.sidebar.caption(f"Нет данных по {c_type}")

if st.sidebar.button("Выйти из системы"):
    st.session_state['auth'] = False
    st.session_state['active_role'] = None
    st.rerun()

# --- 4. ОСНОВНОЙ КОНТЕНТ (ВЫЗОВ ИНТЕРФЕЙСОВ) ---
# Важно: сверяем с названиями ролей
if st.session_state['active_role'] in ["Сотрудник", "Staff"]:
    show_employee_interface(DB_FILE, DB_COLS)
else:
    # Вызываем интерфейс QA для ролей "QA Менеджер", "QA", "Admin" (если выбран этот режим)
    show_qa_interface(DB_FILE, DB_COLS)
