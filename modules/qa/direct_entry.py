import streamlit as st
import pandas as pd
from datetime import datetime
from config import PROCESSES
from modules.core import log_audit

def show_direct_entry(db_file, db_cols):
    st.subheader("➕ Прямое внесение данных (QA/Аудит)")
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    with st.form("qa_direct_form"):
        d_src = st.selectbox("Источник обнаружения:", ["IAProc", "IAPrj", "EA", "Ins", "SP/Reg"])
        d_code = st.selectbox("Код процесса:", list(PROCESSES.keys()), format_func=lambda x: f"{x} - {PROCESSES[x]['full_name']}")
        d_cat = st.selectbox("Категория НС:", ["IntMinor", "IntMajor", "IntCritical", "ExtMinor", "ExtMajor", "ExtCritical", "NewNC"])
        d_desc = st.text_area("Техническое описание")
        d_cnt = st.number_input("Кол-во фактов:", min_value=1, value=1)

        if st.form_submit_button("Внести напрямую"):
            df = pd.read_csv(db_file)
            new_id = len(df) + 1
            new_row = [new_id, now_str, st.session_state.get('u_name','QA'), d_code, PROCESSES[d_code]['full_name'], d_desc, d_desc, d_cnt, d_src, d_cat, "Подтверждено"]
            new_row += [""] * 11 # Пустые поля для CAPA
            
            pd.DataFrame([new_row], columns=db_cols).to_csv(db_file, mode='a', header=False, index=False)
            log_audit(st.session_state.get('u_name','QA'), "Прямой ввод", d_cat)
            st.success("✅ Запись внесена напрямую.")
            st.rerun()
