import streamlit as st
import pandas as pd
import os
from datetime import datetime

def show_capa_investigation(df, db_file, pre_selected_id=None):
    st.subheader("🚨 Реестр CAPA и Расследований (Major, Critical, NewNC)")

    # Фильтруем записи: Major/Critical и все результаты расследований NewNC (кроме Minor)
    capa_df = df[
        (df['Статус'] == "Подтверждено") & 
        (df['Категория'].str.contains('Major|Critical|NewNC', na=False))
    ].copy()

    if not capa_df.empty:
        # 1. СВОДНАЯ ТАБЛИЦА
        open_capa = capa_df[capa_df['CAPA_Done'] != "Да"]
        st.markdown(f"#### 🔍 Открытые дела ({len(open_capa)})")
        st.dataframe(open_capa[['ID', 'Код', 'Категория', 'Описание_QA', 'Corr_Owner', 'CAPA_Owner', 'CAPA_Deadline']], 
                     use_container_width=True, hide_index=True)
        
        st.write("---")
        
        # 2. ИНТЕРФЕЙС УПРАВЛЕНИЯ
        st.markdown("### 🛠️ Карточка управления инцидентом")
        
        available_ids = list(open_capa['ID'].values)
        default_idx = 0
        if pre_selected_id in available_ids:
            default_idx = available_ids.index(pre_selected_id)

        sid = st.selectbox("Выберите ID инцидента для работы:", available_ids, index=default_idx, key="main_sid_selector")
        
        row = open_capa[open_capa['ID'] == sid].iloc[0]

        with st.expander("📝 Исходные данные и описание QA", expanded=False):
            st.write(f"**Процесс:** {row['Код']} - {row['Процесс']}")
            st.write(f"**Описание:** {row['Описание_QA']}")

        # ФОРМА РАБОТЫ (Исправленная)
        with st.form(f"full_capa_form_{sid}"):
            # РАЗДЕЛ 1: КОРРЕКЦИЯ
            st.markdown("#### 🩹 1. КОРРЕКЦИЯ (Устранение последствий)")
            col1, col2, col3 = st.columns(3)
            with col1:
                corr_text = st.text_input("Мероприятие (Коррекция):", value=row.get('Correction', ''), key=f"c_text_{sid}")
            with col2:
                corr_owner = st.text_input("Ответственный (Коррекция):", value=row.get('Corr_Owner', ''), key=f"c_own_{sid}")
            with col3:
                # Пытаемся распарсить дату для календаря
                try:
                    c_date_val = datetime.strptime(row.get('Corr_Deadline'), "%d.%m.%Y")
                except:
                    c_date_val = datetime.now()
                corr_dead = st.date_input("Срок до (Коррекция):", value=c_date_val, key=f"c_date_{sid}")
            
            corr_done = st.checkbox("✅ Коррекция выполнена (Контроль QA)", value=(row.get('Corr_Done') == "Да"), key=f"c_done_{sid}")

            st.write("---")

            # РАЗДЕЛ 2: РАССЛЕДОВАНИЕ
            st.markdown("#### 🔍 2. РАССЛЕДОВАНИЕ (Root Cause Analysis)")
            root_cause = st.text_area("Установленная первопричина (Почему это произошло?):", 
                                     value=row.get('Описание_QA', ''), height=100, key=f"rca_{sid}")

            st.write("---")

            # РАЗДЕЛ 3: CAPA
            st.markdown("#### 🚀 3. CAPA (Предупреждающие действия)")
            capa_desc = st.text_area("Описание системных мер:", value=row.get('CAPA_Plan', ''), height=100, key=f"capa_plan_{sid}")
            
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                capa_owner = st.text_input("Ответственный (CAPA):", value=row.get('CAPA_Owner', ''), key=f"capa_own_{sid}")
            with col_c2:
                try:
                    cp_date_val = datetime.strptime(row.get('CAPA_Deadline'), "%d.%m.%Y")
                except:
                    cp_date_val = datetime.now()
                capa_dead = st.date_input("Срок до (CAPA):", value=cp_date_val, key=f"capa_date_{sid}")
            with col_c3:
                capa_done_check = st.checkbox("🛠️ Меры внедрены", value=(row.get('CAPA_Done') == "Да"), key=f"capa_done_{sid}")

            st.write("---")

            # РАЗДЕЛ 4: ЗАКРЫТИЕ И ЭФФЕКТИВНОСТЬ
            st.markdown("#### 🏁 4. ЗАКРЫТИЕ И ЭФФЕКТИВНОСТЬ")
            eff_comment = st.text_area("Контроль эффективности (Анализ QA):", 
                                      value=row.get('CAPA_Effect', ''),
                                      placeholder="Опишите результаты проверки...", key=f"eff_text_{sid}")
            
            final_close = st.checkbox("🔒 ЗАКРЫТЬ ИНЦИДЕНТ (Архивировать)", key=f"final_close_{sid}")

            # Кнопка сохранения ТЕПЕРЬ ОБЯЗАТЕЛЬНА
            if st.form_submit_button("💾 Сохранить все изменения"):
                if final_close:
                    if not (corr_done and capa_done_check):
                        st.error("Нельзя закрыть инцидент, пока не подтверждено выполнение Коррекции и CAPA!")
                    elif not eff_comment or len(eff_comment) < 15:
                        st.error("Для закрытия необходимо заполнить анализ эффективности!")
                    else:
                        df.loc[df['ID'] == sid, ['Статус', 'CAPA_Done', 'CAPA_Effect']] = ["Закрыто", "Да", eff_comment]
                        st.success(f"Инцидент ID {sid} полностью закрыт.")
                
                # Обновляем все поля
                df.loc[df['ID'] == sid, [
                    'Correction', 'Corr_Owner', 'Corr_Deadline', 'Corr_Done',
                    'Описание_QA', 'CAPA_Plan', 'CAPA_Owner', 'CAPA_Deadline', 'CAPA_Effect'
                ]] = [
                    corr_text, corr_owner, corr_dead.strftime("%d.%m.%Y"), "Да" if corr_done else "Нет",
                    root_cause, capa_desc, capa_owner, capa_dead.strftime("%d.%m.%Y"), eff_comment
                ]
                
                df.to_csv(db_file, index=False)
                st.rerun()

        # АРХИВ
        closed_df = capa_df[capa_df['CAPA_Done'] == "Да"]
        if not closed_df.empty:
            with st.expander(f"📁 Архив закрытых CAPA ({len(closed_df)})"):
                st.dataframe(closed_df[['ID', 'Код', 'Категория', 'CAPA_Plan', 'CAPA_Effect']], 
                             use_container_width=True, hide_index=True)
    else:
        st.info("Нет активных инцидентов Major/Critical.")
