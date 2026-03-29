import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from config import PROCESSES
from modules.analytics import get_nc_analytics

def show_dashboard(df):
    # Инициализация состояния просмотра
    if 'dashboard_view' not in st.session_state:
        st.session_state['dashboard_view'] = 'main'

    # Кнопка возврата в режиме детализации
    if st.session_state['dashboard_view'] != 'main':
        if st.button("⬅️ Вернуться к общему обзору"):
            st.session_state['dashboard_view'] = 'main'
            st.rerun()

    st.write("---")

    # --- ВСПОМОГАТЕЛЬНЫЕ РАСЧЕТЫ ---
    now_dt = datetime.now()

    def get_diff(d_str):
        if pd.isna(d_str) or d_str in ["", "TBD"]: return 999
        try: 
            return (pd.to_datetime(d_str, dayfirst=True, errors='coerce') - now_dt).days
        except: 
            return 999

    # --- ПОДГОТОВКА ДАННЫХ ДЛЯ НС ---
    # 1. Ожидают верификации
    v_list = df[df['Статус'] == "На проверке"]

    # 2. Ожидают планирования коррекций (Minor)
    m_plan = df[
        (df['Статус'] == "На проверке") |
        ((df['Статус'] == "Подтверждено") & 
         (df['Категория'].str.contains('Minor', na=False)) & 
         (df['Correction'].isna() | (df['Correction'] == "")))
    ]

    # 3. Ожидают планирования CAPA (Major/Critical)
    c_plan = df[
        (df['Статус'] == "Подтверждено") & 
        (df['Категория'].str.contains('Major|Critical', na=False)) & 
        (df['CAPA_Plan'].isna() | (df['CAPA_Plan'] == ""))
    ]

    # 4. Новые НС (NewNC)
    n_nc = df[df['Категория'] == "NewNC"]

    # 5. Ближайший контроль (7 дней)
    soon_df = df[
        ((df['Corr_Deadline'].apply(get_diff) <= 7) & (df['Corr_Deadline'].apply(get_diff) >= 0) & (df['Corr_Done'] != "Да")) |
        ((df['CAPA_Deadline'].apply(get_diff) <= 7) & (df['CAPA_Deadline'].apply(get_diff) >= 0) & (df['CAPA_Done'] != "Да"))
    ]

    # 6. Просрочена проверка
    over_df = df[
        ((df['Corr_Deadline'].apply(get_diff) < 0) & (df['Corr_Done'] != "Да")) |
        ((df['CAPA_Deadline'].apply(get_diff) < 0) & (df['CAPA_Done'] != "Да"))
    ]

    # 7. EWMA
    ewma_triggered = []
    for p_code in PROCESSES.keys():
        for c_type in ["IntMinor", "ExtMinor"]:
            check_data = get_nc_analytics(p_code, c_type)
            if not check_data.empty:
                if check_data.iloc[-1]['Alert']:
                    ewma_triggered.append(f"{p_code}({c_type})")

    # ==========================================
    # РЕЖИМ 1: ГЛАВНЫЙ ЭКРАН (ОБЗОР В 3 КОЛОНКИ)
    # ==========================================
    if st.session_state['dashboard_view'] == 'main':
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 📅 Планирование аудитов")
            st.markdown("#### **Внутренние аудиты**")
            st.info("**План ВА 2026**")
            if st.button("🔍 Ближайшие ВА (детали)"): 
                st.session_state['dashboard_view'] = 'audit_va'
                st.rerun()

            st.markdown("---")
            st.markdown("#### **Внешние аудиты**")
            if st.button("🌍 Рэддис, 09-12.07.2026"): 
                st.session_state['dashboard_view'] = 'audit_ext'
                st.rerun()

        with col2:
            st.markdown("### 📝 Управление НС")
            
            if st.button(f"1. Ожидают верификации: {len(v_list)}"): 
                st.session_state['dashboard_view'] = 'nc_v'; st.rerun()
            
            if st.button(f"2. Ожидают планы коррекций (Minor): {len(m_plan)}"): 
                st.session_state['dashboard_view'] = 'nc_m'; st.rerun()
            
            if st.button(f"3. Ожидают планы CAPA: {len(c_plan)}"): 
                st.session_state['dashboard_view'] = 'nc_c'; st.rerun()
            
            if st.button(f"4. Новые НС (NewNC): {len(n_nc)}"): 
                st.session_state['dashboard_view'] = 'nc_new'; st.rerun()
            
            if st.button(f"5. Ближайший контроль (7 дн.): {len(soon_df)}"): 
                st.session_state['dashboard_view'] = 'nc_soon'; st.rerun()
            
            if st.button(f"🚨 6. Просрочена проверка: {len(over_df)}"): 
                st.session_state['dashboard_view'] = 'nc_over'; st.rerun()

            ewma_count = len(ewma_triggered)
            btn_label = f"📈 7. Сработал EWMA: {ewma_count}"
            if ewma_count > 0:
                st.error(btn_label)
                if st.button("🔍 Посмотреть алерты", key="ewma_btn"):
                    st.session_state['dashboard_view'] = 'nc_ewma'; st.rerun()
            else:
                if st.button(btn_label):
                    st.session_state['dashboard_view'] = 'nc_ewma'; st.rerun()

        with col3:
            st.markdown("### ⚖️ Управление рисками")
            st.info("Раздел EWMA-3 (Риски процессов)")
            st.caption("Ожидание настройки аналитики...")

    # ==========================================
    # РЕЖИМ 2: ДЕТАЛИЗАЦИЯ (ИНТЕРАКТИВНАЯ)
    # ==========================================
    
    elif st.session_state['dashboard_view'] == 'nc_v':
        st.subheader("📥 (1) Ожидают верификации")
        if not v_list.empty:
            ev = st.dataframe(v_list[['ID', 'Дата_Время', 'Автор', 'Код', 'Описание_OPS']], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
            if ev.selection.rows:
                st.session_state['active_tab'] = "🔍 Верификация"
                st.session_state['selected_nc_id'] = v_list.iloc[ev.selection.rows[0]]['ID']
                st.rerun()
        else: st.success("Все верифицировано!")

    elif st.session_state['dashboard_view'] == 'nc_m':
        st.subheader("📝 (2) Ожидают планы коррекций (Minor)")
        if not m_plan.empty:
            ev = st.dataframe(m_plan[['ID', 'Код', 'Категория', 'Описание_QA']], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
            if ev.selection.rows:
                st.session_state['active_tab'] = "📄 Реестр (Minor)"
                st.session_state['selected_nc_id'] = m_plan.iloc[ev.selection.rows[0]]['ID']
                st.rerun()

    elif st.session_state['dashboard_view'] == 'nc_c':
        st.subheader("🚨 (3) Ожидают планы CAPA")
        if not c_plan.empty:
            ev = st.dataframe(c_plan[['ID', 'Код', 'Категория', 'Описание_QA']], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
            if ev.selection.rows:
                st.session_state['active_tab'] = "🚨 CAPA / Расследования"
                st.session_state['selected_nc_id'] = c_plan.iloc[ev.selection.rows[0]]['ID']
                st.rerun()

    elif st.session_state['dashboard_view'] == 'nc_new':
        st.subheader("🆕 (4) Новые несоответствия (NewNC)")
        if not n_nc.empty:
            ev = st.dataframe(n_nc[['ID', 'Дата_Время', 'Код', 'Описание_QA']], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
            if ev.selection.rows:
                st.session_state['active_tab'] = "🔍 Верификация"
                st.session_state['selected_nc_id'] = n_nc.iloc[ev.selection.rows[0]]['ID']
                st.rerun()

    elif st.session_state['dashboard_view'] == 'nc_soon':
        st.subheader("📅 (5) Ближайший контроль (7 дней)")
        if not soon_df.empty:
            ev = st.dataframe(soon_df[['ID', 'Код', 'Категория', 'Corr_Deadline', 'CAPA_Deadline']], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
            if ev.selection.rows:
                row = soon_df.iloc[ev.selection.rows[0]]
                st.session_state['active_tab'] = "📄 Реестр (Minor)" if "Minor" in str(row['Категория']) else "🚨 CAPA / Расследования"
                st.session_state['selected_nc_id'] = row['ID']
                st.rerun()

    elif st.session_state['dashboard_view'] == 'nc_over':
        st.error("⏰ (6) ПРОСРОЧЕННЫЕ ПРОВЕРКИ")
        if not over_df.empty:
            ev = st.dataframe(over_df[['ID', 'Код', 'Категория', 'Corr_Deadline', 'CAPA_Deadline']], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
            if ev.selection.rows:
                row = over_df.iloc[ev.selection.rows[0]]
                st.session_state['active_tab'] = "📄 Реестр (Minor)" if "Minor" in str(row['Категория']) else "🚨 CAPA / Расследования"
                st.session_state['selected_nc_id'] = row['ID']
                st.rerun()

    elif st.session_state['dashboard_view'] == 'nc_ewma':
        st.subheader("📈 (7) Статус EWMA")
        if ewma_triggered:
            st.warning(f"Обнаружены статистические отклонения в процессах: {', '.join(ewma_triggered)}")
        else: st.info("Превышений не обнаружено.")

    elif st.session_state['dashboard_view'] in ['audit_va', 'audit_ext', 'audit_lab']:
        st.info("Раздел в разработке")
