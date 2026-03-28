import streamlit as st
import pandas as pd
from datetime import datetime
from config import PROCESSES

def show_audit_planner(db_file):
    st.subheader("📅 Планирование и мониторинг аудитов")
    
    tab_int, tab_ext, tab_prj = st.tabs([
        "🏢 Внутренние (ISO 19011)", 
        "🌍 Внешние / Сертификационные", 
        "🏗️ Аудиты проектов"
    ])

    with tab_int:
        st.markdown("#### Программа внутренних аудитов (ПВА)")
        with st.form("int_audit_form"):
            col1, col2 = st.columns(2)
            a_proc = col1.selectbox("Процесс для аудита:", list(PROCESSES.keys()), 
                                    format_func=lambda x: f"{x} - {PROCESSES[x]['full_name']}")
            a_date = col2.date_input("Плановая дата:")
            
            col3, col4 = st.columns(2)
            a_lead = col3.text_input("Ведущий аудитор:")
            a_team = col4.text_input("Члены группы:")
            
            a_scope = st.text_area("Область аудита (Scope) / Критерии:")
            
            if st.form_submit_button("Добавить в план ПВА"):
                st.success(f"Аудит процесса {a_proc} запланирован на {a_date}")

    with tab_ext:
        st.markdown("#### Реестр внешних проверок")
        with st.form("ext_audit_form"):
            e_company = st.text_input("Проверяющая организация (Орган по сертификации / Клиент):")
            
            col1, col2, col3 = st.columns(3)
            e_date = col1.text_input("Ориентировочные даты:", placeholder="Напр: Октябрь 2024")
            e_type = col2.selectbox("Формат:", ["Очный", "Дистанционный", "Гибридный"])
            e_standard = col3.text_input("Стандарт / Основание:", value="ISO 9001:2015")
            
            e_prep = st.text_area("Что подготовить (Документы / Ответственные):", 
                                 placeholder="Подготовить записи по обучению, отчеты по рискам...")
            
            if st.form_submit_button("Зафиксировать в графике"):
                st.info(f"Внешний аудит ({e_company}) внесен в лист ожидания.")

    with tab_prj:
        st.markdown("#### Технические аудиты проектов")
        
        # Вставляем ваше пояснение о будущем функционале
        st.info("""
            💡 **План развития:** В этом блоке будет реализован функционал цифрового взаимодействия с лабораторией. 
            Заведующий лабораторией сможет отправлять задачи и отчетные файлы на проверку напрямую через систему (минуя почту). 
            Система будет автоматически подгружать файлы, проводить первичный контроль и отображать статус готовности в режиме реального времени.
        """)
        
        with st.form("prj_audit_form"):
            p_name = st.text_input("Наименование проекта / Код:")
            p_milestone = st.selectbox("Этап контроля:", ["Старт", "Проектирование", "Реализация", "Сдача"])
            
            # Добавим поле для загрузки (пока визуальное)
            st.file_uploader("Загрузить файлы проекта (тест):", accept_multiple_files=True, disabled=True)
            
            p_check = st.text_area("Ключевые точки контроля:")
            
            if st.form_submit_button("Запланировать проверку проекта"):
                st.write("Запланировано.")

    # Общий календарный вид
    st.write("---")
    st.caption("Календарный график аудитов находится в стадии интеграции.")
