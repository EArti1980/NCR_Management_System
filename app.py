import streamlit as st
import pandas as pd
import os
from config import PROCESSES
# Импортируем функции из наших модулей
from modules.auth import show_auth_page
from modules.analytics import get_nc_analytics
from modules.ui_employee import show_employee_interface
# ИСПРАВЛЕННЫЙ ИМПОРТ: обращаемся к файлу напрямую
from modules.ui_qa import show_qa_interface

# --- 1. ИНИЦИАЛИЗАЦИЯ И НАСТРОЙКИ ---
st.set_page_config(page_title="Система управления НС", layout="wide")
DB_FILE = 'nc_main_data.csv'

# РАСШИРЕННЫЙ СПИСОК КОЛОНОК (согласно PDF)
DB_COLS = [
    'ID', 'Дата_Время', 'Автор', 'Код', 'Процесс', 'Описание_OPS', 'Описание_QA', 
    'Кол_во', 'Источник', 'Категория', 'Статус',
    'Correction', 'Corr_Deadline', 'Corr_Owner', 'Corr_Done',
    'Root_Cause', 'CAPA_Plan', 'CAPA_Deadline', 'CAPA_Owner', 'CAPA_Done',
    'QA_Comment', 'Is_Recurrent'
]

# Проверка наличия базы при старте
if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=DB_COLS).to_csv(DB_FILE, index=False)

# Инициализация состояния авторизации
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

# --- 2. ПРОВЕРКА АВТОРИЗАЦИИ ---
if not st.session_state['auth']:
    show_auth_page()
    st.stop() 

# --- 3. БОКОВАЯ ПАНЕЛЬ (SIDEBAR) ---
st.sidebar.success(f"👤 {st.session_state['u_name']}")

# Логика ролей для Админа
if st.session_state['u_role'] == "Admin":
    st.sidebar.warning("🛠️ АДМИН-ПАНЕЛЬ")
    st.session_state['active_role'] = st.sidebar.radio(
        "Переключить интерфейс на:", 
        ["Сотрудник", "QA Менеджер"]
    )

# Блок графиков EWMA
if st.sidebar.checkbox("📊 Показать графики трендов"):
    st.sidebar.markdown("---")
    p_an = st.sidebar.selectbox("Выберите процесс:", list(PROCESSES.keys()))
    for c_type in ["IntMinor", "ExtMinor"]:
        data_plot = get_nc_analytics(p_an, c_type)
        if not data_plot.empty:
            is_alert = data_plot.iloc[-1]['Alert']
            st.sidebar.write(f"{'🔴 ALERT' if is_alert else '📈'} **{c_type}**")
            st.sidebar.line_chart(data_plot, x='Month_Str', y=['EWMA', 'UCL'])
        else:
            st.sidebar.caption(f"Нет данных по {c_type}")

if st.sidebar.button("Выйти из системы"):
    st.session_state['auth'] = False
    st.rerun()

# --- 4. ОСНОВНОЙ КОНТЕНТ (ВЫЗОВ ИНТЕРФЕЙСОВ) ---
if st.session_state.get('active_role') == "Сотрудник":
    show_employee_interface(DB_FILE, DB_COLS)
else:
    show_qa_interface(DB_FILE, DB_COLS)
