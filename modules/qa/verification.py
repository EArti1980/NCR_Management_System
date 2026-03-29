import streamlit as st
import pandas as pd
import os
from datetime import datetime
from config import PROCESSES, DB_COLS, SOURCES
from modules.core import log_audit

def show_verification(df, db_file, pre_selected_id=None):
    # КНОПКА ВОЗВРАТА В ДАШБОРД
    if st.button("⬅️ Вернуться в Дашборд QA"):
        st.session_state['active_tab'] = "📊 Дашборд QA"
        st.session_state['dashboard_view'] = 'main'
        st.rerun()

    st.subheader("🔍 Верификация и управление NewNC")
    
    # Проверка авторизации QA
    if 'u_name' not in st.session_state or not st.session_state['u_name']:
        st.warning("⚠️ Для работы необходимо указать ФИО и должность в разделе 'Прямой ввод' или 'Профиль'.")
        return

    now_dt = datetime.now()
    now_str = now_dt.strftime("%d.%m.%Y %H:%M")
    
    # Фильтруем записи: либо на проверке, либо уже отмеченные как NewNC
    pending = df[(df['Статус'] == "На проверке") | (df['Категория'] == "NewNC")]
    
    if not pending.empty:
        # Автовыбор ID при переходе из дашборда
        default_idx = 0
        if pre_selected_id is not None and pre_selected_id in pending['ID'].values:
            default_idx = list(pending['ID']).index(pre_selected_id)

        sid = st.selectbox(
            "Выберите ID записи:", 
            pending['ID'], 
            index=default_idx,
            key="sel_verify"
        )
        
        # Данные текущей строки
        row = pending[pending['ID'] == sid].iloc[0]
        
        # Идентификация автора (ФИО + Должность)
        author_info = f"{row['Автор']} ({row.get('Должность', 'Должность не указана')})"
        st.warning(f"📌 **Зафиксировал:** {author_info} | **Дата:** {row['Дата_Время']}")
        st.write(f"**Оригинал описания (OPS):** {row['Описание_OPS']}")
        
        st.write("---")
        
        # --- ВЫБОР ПРОЦЕССА, ИСТОЧНИКА И ПРИЗНАКА NewNC ---
        col1, col2, col3 = st.columns(3)
        with col1:
            n_code = st.selectbox(
                "Код процесса:", 
                options=list(PROCESSES.keys()),
                index=list(PROCESSES.keys()).index(row['Код']) if row['Код'] in PROCESSES else 0,
                format_func=lambda x: f"{x} - {PROCESSES[x]['full_name']}"
            )
        with col2:
            # ВЫБОР ИСТОЧНИКА (согласно п. 1.1 PDF)
            n_source = st.selectbox(
                "Источник НС:",
                options=list(SOURCES.keys()),
                format_func=lambda x: f"{x} - {SOURCES[x]}",
                help="Укажите источник обнаружения несоответствия"
            )
        with col3:
            is_new_init = True if row['Категория'] == "NewNC" else False
            is_new_nc = st.checkbox("🚩 Это NewNC", value=is_new_init)

        # =========================================================================
        # БЛОК УПРАВЛЕНИЯ НЕИЗВЕСТНЫМ НС (NewNC)
        # =========================================================================
        if is_new_nc:
            st.error("🛠️ ПРОТОКОЛ РАССЛЕДОВАНИЯ NewNC")
            
            res_investigation = st.text_area("Результаты расследования (причины, масштаб, влияние):", 
                                            value=row.get('Описание_QA', ''))
            
            col_cat, col_date = st.columns(2)
            with col_cat:
                final_cat = st.selectbox(
                    "Итоговая категория:",
                    ["NewMinor", "NewMajor", "NewCritical", "NewNC (в процессе)"],
                    index=3 if row['Категория'] == "NewNC" else 0
                )
            with col_date:
                st.caption(f"Дата категорирования: {now_str if 'New' in final_cat else 'Ожидание'}")

            st.write("---")
            
            st.markdown("### 🩹 Коррекция")
            col_corr1, col_corr2 = st.columns(2)
            with col_corr1:
                corr_text = st.text_input("Что сделать (Коррекция):", value=row.get('Correction', ''))
                corr_owner = st.text_input("Ответственный (Коррекция):", value=row.get('Corr_Owner', ''))
            with col_corr2:
                corr_deadline = st.date_input("Срок коррекции до:", key="c_dead")
                corr_done = st.checkbox("Отметка о выполнении (Коррекция)", value=(row.get('Corr_Done') == "Да"))

            st.write("---")

            st.markdown("### 🚀 CAPA (Предупреждающие действия)")
            capa_desc = st.text_area("Описание CAPA:", value=row.get('CAPA_Plan', ''))
            
            col_capa1, col_capa2 = st.columns(2)
            with col_capa1:
                capa_owner = st.text_input("Ответственный (CAPA):", value=row.get('CAPA_Owner', ''))
                capa_eff = st.text_input("Контроль эффективности (QA):", value=row.get('CAPA_Effect', ''))
            with col_capa2:
                capa_deadline = st.date_input("Срок CAPA до:", key="capa_dead")
                capa_done = st.checkbox("CAPA закрыта", value=(row.get('CAPA_Done') == "Да"))

            if st.button("💾 Сохранить и обновить протокол NewNC"):
                df.loc[df['ID'] == sid, [
                    'Источник', 'Код', 'Процесс', 'Описание_QA', 'Категория', 'Статус',
                    'Correction', 'Corr_Owner', 'Corr_Deadline', 'Corr_Done',
                    'CAPA_Plan', 'CAPA_Owner', 'CAPA_Deadline', 'CAPA_Done', 'CAPA_Effect',
                    'NewNC_Stage'
                ]] = [
                    n_source, n_code, PROCESSES[n_code]['full_name'], res_investigation, final_cat, "Подтверждено",
                    corr_text, corr_owner, corr_deadline.strftime("%d.%m.%Y"), "Да" if corr_done else "Нет",
                    capa_desc, capa_owner, capa_deadline.strftime("%d.%m.%Y"), "Да" if capa_done else "Нет", capa_eff,
                    "Завершено" if (corr_done and capa_done) else "В работе"
                ]
                
                df.to_csv(db_file, index=False)
                
                qa_info = f"{st.session_state['u_name']} ({st.session_state.get('u_job', 'Должность не указана')})"
                log_audit(qa_info, "NewNC Update", f"ID {sid} -> {final_cat}")
                
                st.success("✅ Протокол NewNC успешно обновлен.")
                st.rerun()

        # =========================================================================
        # БЛОК СТАНДАРТНОЙ ВЕРИФИКАЦИИ
        # =========================================================================
        else:
            with st.form("qa_verify_form"):
                cat = st.selectbox(
                    "Присвоить стандартную категорию:", 
                    ["IntMinor", "IntMajor", "IntCritical", "ExtMinor", "ExtMajor", "ExtCritical"],
                    key="sel_cat_std"
                )
                
                n_desc = st.text_area("Техническое описание (QA):", 
                                     value=row['Описание_QA'] if pd.notna(row['Описание_QA']) and row['Описание_QA'] != "" else row['Описание_OPS'])
                
                n_cnt = st.number_input("Уточненное количество:", value=int(row['Кол_во']), min_value=1)
                
                if st.form_submit_button("Утвердить и перевести в Реестр"):
                    df.loc[df['ID'] == sid, 
                           ['Дата_Время', 'Источник', 'Код', 'Процесс', 'Описание_QA', 'Кол_во', 'Категория', 'Статус']] = \
                           [now_str, n_source, n_code, PROCESSES[n_code]['full_name'], n_desc, n_cnt, cat, "Подтверждено"]
                    
                    df.to_csv(db_file, index=False)
                    
                    qa_info = f"{st.session_state['u_name']} ({st.session_state.get('u_job', 'Должность не указана')})"
                    log_audit(qa_info, "Верификация", f"ID {sid} -> {cat}")
                    
                    st.success(f"✅ Инцидент ID {sid} верифицирован.")
                    st.rerun()
    else:
        st.info("Нет записей, ожидающих проверки QA.")
