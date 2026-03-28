import streamlit as st
import pandas as pd
from datetime import datetime
# Импортируем подмодули из новой папки qa/
from modules.qa.dashboard import show_dashboard
from modules.qa.verification import show_verification
from modules.qa.direct_entry import show_direct_entry
from modules.qa.minor_management import show_minor_management
from modules.qa.capa_investigation import show_capa_investigation
from modules.qa.audit_planner import show_audit_planner # Вот этот импорт важен

def show_qa_interface(db_file, db_cols):
    st.header("🛡️ Управление качеством (QA)")
    
    # Загружаем БД один раз для всех вкладок
    if not pd.io.common.file_exists(db_file):
        st.error(f"Файл базы данных {db_file} не найден!")
        return
        
    df_all = pd.read_csv(db_file)
    
    # ВАЖНО: Здесь должно быть 6 вкладок (t0 - t5)
    t0, t1, t2, t3, t4, t5 = st.tabs([
        "📊 Дашборд QA",
        "🔍 Верификация", 
        "➕ Прямой ввод", 
        "📄 Реестр (Minor)",
        "🚨 CAPA / Расследования",
        "📅 Аудиты" # Шестая вкладка
    ])

    with t0:
        show_dashboard(df_all)

    with t1:
        show_verification(df_all, db_file)

    with t2:
        show_direct_entry(db_file, db_cols)

    with t3:
        show_minor_management(df_all, db_file)

    with t4:
        show_capa_investigation(df_all, db_file)

    with t5:
        # Вызов модуля планировщика аудитов
        show_audit_planner(db_file)
