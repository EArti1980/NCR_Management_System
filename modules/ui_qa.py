import streamlit as st
import pandas as pd
import os
from modules.qa.dashboard import show_dashboard
from modules.qa.verification import show_verification
from modules.qa.direct_entry import show_direct_entry
from modules.qa.minor_management import show_minor_management
from modules.qa.capa_investigation import show_capa_investigation
from modules.qa.audit_planner import show_audit_planner
from modules.qa.risk_management import show_risk_management

def show_qa_interface(db_file, db_cols):
    st.header("🛡️ Управление качеством (QA)")
    
    if not os.path.exists(db_file):
        st.error(f"БД {db_file} не найдена!")
        return
        
    df_all = pd.read_csv(db_file)

    # Список вкладок (включая 7-ю вкладку Рисков)
    tabs_list = [
        "📊 Дашборд QA", 
        "🔍 Верификация", 
        "➕ Прямой ввод", 
        "📑 Реестр НС", 
        "🚨 CAPA / Расследования", 
        "📅 Аудиты",
        "⚖️ Управление рисками"
    ]

    if 'active_tab' not in st.session_state:
        st.session_state['active_tab'] = "📊 Дашборд QA"

    try:
        current_index = tabs_list.index(st.session_state['active_tab'])
    except:
        current_index = 0

    selected_tab = st.radio("Навигация:", tabs_list, index=current_index, 
                            horizontal=True, label_visibility="collapsed")

    if selected_tab != st.session_state['active_tab']:
        st.session_state['active_tab'] = selected_tab
        st.rerun()

    # Универсальная кнопка возврата
    if st.session_state['active_tab'] != "📊 Дашборд QA":
        if st.button("⬅️ Вернуться в Дашборд QA", key="global_back_btn"):
            st.session_state['active_tab'] = "📊 Дашборд QA"
            if 'dashboard_view' in st.session_state:
                st.session_state['dashboard_view'] = 'main'
            st.rerun()

    st.write("---")
    
    pre_id = st.session_state.get('selected_nc_id', None)

    # ЛОГИКА ПЕРЕКЛЮЧЕНИЯ ВКЛАДОК
    if st.session_state['active_tab'] == "📊 Дашборд QA":
        show_dashboard(df_all)
    elif st.session_state['active_tab'] == "🔍 Верификация":
        show_verification(df_all, db_file, pre_id)
    elif st.session_state['active_tab'] == "➕ Прямой ввод":
        show_direct_entry(db_file, db_cols)
    elif st.session_state['active_tab'] == "📑 Реестр НС":
        show_minor_management(df_all, db_file, pre_id)
    elif st.session_state['active_tab'] == "🚨 CAPA / Расследования":
        show_capa_investigation(df_all, db_file, pre_id)
    elif st.session_state['active_tab'] == "📅 Аудиты":
        show_audit_planner(db_file)
    elif st.session_state['active_tab'] == "⚖️ Управление рисками":
        show_risk_management(df_all)
    
    # Очистка id после использования, если мы не во вкладках верификации/реестра
    if 'selected_nc_id' in st.session_state and st.session_state['active_tab'] not in ["🔍 Верификация", "📑 Реестр НС", "🚨 CAPA / Расследования"]:
        del st.session_state['selected_nc_id']
