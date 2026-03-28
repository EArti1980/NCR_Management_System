import streamlit as st
import pandas as pd
from modules.core import log_audit

def show_capa_investigation(df, db_file):
    st.subheader("🚨 Реестр открытых расследований (CAPA)")
    
    # Инциденты Major/Critical, где CAPA еще не закрыто
    to_capa = df[
        (df['Категория'].str.contains('Major|Critical|NewNC', na=False)) &
        (df['CAPA_Done'] != "Да") &
        (df['Статус'] == "Подтверждено")
    ]

    if to_capa.empty:
        st.success("✅ Все критические инциденты отработаны.")
    else:
        for _, r in to_capa.iterrows():
            with st.expander(f"🆘 ID {r['ID']} | {r['Код']} | {r['Категория']} (от {r['Дата_Время']})"):
                st.write(f"**Описание:** {r['Описание_QA']}")

                # МЕХАНИЗМ ПАМЯТИ: Проверка на повторность по коду процесса
                past = df[(df['Код'] == r['Код']) & (df['ID'] != r['ID']) &
                          (df['Категория'] == r['Категория']) &
                          (df['CAPA_Done'] == "Да")]
                if not past.empty:
                    st.error(f"⚠️ ВНИМАНИЕ: Это повторное событие! Аналогичный инцидент был закрыт ранее (ID {past.iloc[-1]['ID']}).")

                with st.form(f"capa_form_{r['ID']}"):
                    st.markdown("### 1. КОРРЕКЦИЯ")
                    col1, col2, col3 = st.columns(3)
                    c_text = col1.text_input("Необходимая коррекция", value=r['Correction'] if pd.notna(r['Correction']) else "")
                    c_date = col2.text_input("Срок", value=r['Corr_Deadline'] if pd.notna(r['Corr_Deadline']) else "")
                    c_owner = col3.text_input("Ответственный", value=r['Corr_Owner'] if pd.notna(r['Corr_Owner']) else "")
                    c_done = st.checkbox("Коррекция выполнена (QA)", value=(r['Corr_Done'] == "Да"))

                    st.markdown("### 2. АНАЛИЗ ПРИЧИН И CAPA")
                    cause = st.text_area("Анализ коренных причин:", value=r['Root_Cause'] if pd.notna(r['Root_Cause']) else "")
                    capa_plan = st.text_area("План мероприятий (CAPA):", value=r['CAPA_Plan'] if pd.notna(r['CAPA_Plan']) else "")
                    
                    col4, col5 = st.columns(2)
                    cp_date = col4.text_input("Срок реализации CAPA", value=r['CAPA_Deadline'] if pd.notna(r['CAPA_Deadline']) else "")
                    cp_owner = col5.text_input("Ответственный за выполнение", value=r['CAPA_Owner'] if pd.notna(r['CAPA_Owner']) else "")

                    st.markdown("### 3. ЗАКРЫТИЕ И ЭФФЕКТИВНОСТЬ")
                    cp_done = st.checkbox("CAPA выполнено и проверено (QA)", value=(r['CAPA_Done'] == "Да"))
                    q_comm = st.text_input("Комментарий QA по эффективности", value=r['QA_Comment'] if pd.notna(r['QA_Comment']) else "")

                    if st.form_submit_button("Сохранить данные расследования"):
                        df.loc[df['ID'] == r['ID'], 
                                   ['Correction', 'Corr_Deadline', 'Corr_Owner', 'Corr_Done', 
                                    'Root_Cause', 'CAPA_Plan', 'CAPA_Deadline', 'CAPA_Owner', 'CAPA_Done', 'QA_Comment']] = \
                                   [c_text, c_date, c_owner, "Да" if c_done else "Нет", 
                                    cause, capa_plan, cp_date, cp_owner, "Да" if cp_done else "Нет", q_comm]
                        
                        df.to_csv(db_file, index=False)
                        log_audit(st.session_state.get('u_name', 'QA'), "Обновление CAPA", f"ID {r['ID']}")
                        st.success(f"Данные по ID {r['ID']} обновлены.")
                        st.rerun()
