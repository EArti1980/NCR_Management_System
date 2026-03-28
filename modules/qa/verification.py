import streamlit as st
import pandas as pd
from datetime import datetime
from config import PROCESSES
from modules.core import log_audit

def show_verification(df, db_file):
    st.subheader("🔍 Верификация черновиков")
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    pending = df[df['Статус'] == "На проверке"]

    if not pending.empty:
        sid = st.selectbox("Выберите ID записи для проверки:", pending['ID'], key="sel_verify")
        row = pending[pending['ID'] == sid].iloc[0]

        st.warning(f"📌 **Черновик от {row['Автор']}**")
        st.write(f"**Оригинал описания:** {row['Описание_OPS']}")

        n_code = st.selectbox(
            "Уточнить код процесса:", 
            options=list(PROCESSES.keys()),
            index=list(PROCESSES.keys()).index(row['Код']) if row['Код'] in PROCESSES else 0,
            format_func=lambda x: f"{x} - {PROCESSES[x]['full_name']}",
            key="sel_proc"
        )

        cat = st.selectbox(
            "Присвоить категорию:", 
            ["IntMinor", "IntMajor", "IntCritical", "ExtMinor", "ExtMajor", "ExtCritical", "NewNC"],
            key="sel_cat"
        )

        is_critical = any(kw in cat for kw in ["Major", "Critical"]) or cat == "NewNC"

        with st.form("qa_verify_form"):
            n_desc = st.text_area("Техническое описание (QA):", 
                                value=row['Описание_QA'] if pd.notna(row['Описание_QA']) and row['Описание_QA'] != "" else row['Описание_OPS'])
            n_cnt = st.number_input("Уточненное количество:", value=int(row['Кол_во']), min_value=1)

            if st.form_submit_button("Утвердить и внести в базу"):
                df.loc[df['ID'] == sid, 
                      ['Дата_Время', 'Код', 'Процесс', 'Описание_QA', 'Кол_во', 'Категория', 'Статус']] = \
                      [now_str, n_code, PROCESSES[n_code]['full_name'], n_desc, n_cnt, cat, "Подтверждено"]
                
                df.to_csv(db_file, index=False)
                log_audit(st.session_state.get('u_name','QA'), "Верификация", f"ID {sid} -> {cat}")
                st.success(f"✅ Инцидент ID {sid} подтвержден.")
                st.rerun()
    else:
        st.info("Нет новых записей для верификации.")
