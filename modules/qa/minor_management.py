import streamlit as st
import pandas as pd
from modules.core import log_audit

def show_minor_management(df, db_file):
    st.subheader("📄 Реестр и управление коррекциями (Minor)")
    
    minor_df = df[(df['Статус'] == "Подтверждено") & (df['Категория'].str.contains('Minor', na=False))]
    
    if minor_df.empty:
        st.info("Нет Minor-событий для коррекций.")
    else:
        for _, r in minor_df.iterrows():
            icon = "✅" if r['Corr_Done'] == "Да" else "⏳"
            with st.expander(f"{icon} ID {r['ID']} | {r['Код']} | {r['Категория']}"):
                st.write(f"**Описание:** {r['Описание_QA']}")
                
                with st.form(f"minor_form_{r['ID']}"):
                    st.markdown("### 1. КОРРЕКЦИЯ")
                    c1, c2, c3 = st.columns(3)
                    m_corr = c1.text_input("Коррекция", value=r['Correction'] if pd.notna(r['Correction']) else "")
                    m_dead = c2.text_input("Срок", value=r['Corr_Deadline'] if pd.notna(r['Corr_Deadline']) else "")
                    m_own = c3.text_input("Ответственный", value=r['Corr_Owner'] if pd.notna(r['Corr_Owner']) else "")
                    m_done = st.checkbox("Выполнено (QA)", value=(r['Corr_Done'] == "Да"))
                    
                    st.write("---")
                    q_capa = st.radio("Требуется полномасштабная CAPA?", ["Нет", "Да"], 
                                     index=1 if (pd.notna(r['CAPA_Plan']) and r['CAPA_Plan'] != "") else 0,
                                     key=f"q_capa_{r['ID']}")
                    
                    if q_capa == "Да":
                        st.markdown("### 2. CAPA")
                        m_cause = st.text_area("Причина", value=r['Root_Cause'] if pd.notna(r['Root_Cause']) else "")
                        m_plan = st.text_area("План", value=r['CAPA_Plan'] if pd.notna(r['CAPA_Plan']) else "")
                        m_c_done = st.checkbox("CAPA проверена (QA)", value=(r['CAPA_Done'] == "Да"))

                    if st.form_submit_button("Сохранить"):
                        df.loc[df['ID'] == r['ID'], ['Correction', 'Corr_Deadline', 'Corr_Owner', 'Corr_Done']] = \
                            [m_corr, m_dead, m_own, "Да" if m_done else "Нет"]
                        if q_capa == "Да":
                            df.loc[df['ID'] == r['ID'], ['Root_Cause', 'CAPA_Plan', 'CAPA_Done']] = \
                                [m_cause, m_plan, "Да" if m_c_done else "Нет"]
                        df.to_csv(db_file, index=False)
                        st.success("Данные сохранены.")
                        st.rerun()
