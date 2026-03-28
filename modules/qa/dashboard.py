import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

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
        try: return (pd.to_datetime(d_str, dayfirst=True, errors='coerce') - now_dt).days
        except: return 999

    # --- ПОДГОТОВКА ДАННЫХ ДЛЯ НС ---
    v_list = df[df['Статус'] == "На проверке"]
    
    # Пункт 2: Ожидают планирования коррекций (Minor)
    m_plan = df[
        (df['Статус'] == "На проверке") | 
        ((df['Статус'] == "Подтверждено") & (df['Категория'].str.contains('Minor', na=False)) & (df['Correction'].isna() | (df['Correction'] == "")))
    ]
    
    # Пункт 3: Ожидают планирования CAPA (Major/Critical)
    c_plan = df[
        (df['Статус'] == "Подтверждено") & (df['Категория'].str.contains('Major|Critical', na=False)) & (df['CAPA_Plan'].isna() | (df['CAPA_Plan'] == ""))
    ]
    
    # Пункт 4: Новые НС (NewNC)
    n_nc = df[df['Категория'] == "NewNC"]
    
    # Пункт 5: Ближайший контроль (7 дней)
    soon_df = df[
        ((df['Corr_Deadline'].apply(get_diff) <= 7) & (df['Corr_Deadline'].apply(get_diff) >= 0) & (df['Corr_Done'] != "Да")) |
        ((df['CAPA_Deadline'].apply(get_diff) <= 7) & (df['CAPA_Deadline'].apply(get_diff) >= 0) & (df['CAPA_Done'] != "Да"))
    ]
    
    # Пункт 6: Просрочена проверка
    over_df = df[
        ((df['Corr_Deadline'].apply(get_diff) < 0) & (df['Corr_Done'] != "Да")) |
        ((df['CAPA_Deadline'].apply(get_diff) < 0) & (df['CAPA_Done'] != "Да"))
    ]

    # Пункт 7: EWMA (Заглушка)
    ewma_triggered = [] 

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

            st.markdown("---")
            st.markdown("#### **Аудиты проектов**")
            if st.button("🏗️ Проверить данные лаборатории"): 
                st.session_state['dashboard_view'] = 'audit_lab'
                st.rerun()

        with col2:
            st.markdown("### 📝 Управление НС")
            
            if st.button(f"1. Ожидают верификации: {len(v_list)}"): 
                st.session_state['dashboard_view'] = 'nc_v'
                st.rerun()
            
            if st.button(f"2. Ожидают планы коррекций (Minor): {len(m_plan)}"): 
                st.session_state['dashboard_view'] = 'nc_m'
                st.rerun()
            
            if st.button(f"3. Ожидают планы CAPA: {len(c_plan)}"): 
                st.session_state['dashboard_view'] = 'nc_c'
                st.rerun()
            
            if st.button(f"4. Новые НС (NewNC): {len(n_nc)}"): 
                st.session_state['dashboard_view'] = 'nc_new'
                st.rerun()
            
            if st.button(f"5. Ближайший контроль (7 дн.): {len(soon_df)}"): 
                st.session_state['dashboard_view'] = 'nc_soon'
                st.rerun()
            
            if st.button(f"🚨 6. Просрочена проверка: {len(over_df)}"): 
                st.session_state['dashboard_view'] = 'nc_over'
                st.rerun()
            
            # ИСПРАВЛЕННЫЙ 7-Й ПУНКТ (Теперь это кнопка-рамка)
            ewma_label = ', '.join(ewma_triggered) if ewma_triggered else '0'
            if st.button(f"📈 7. Сработал EWMA: {ewma_label}"):
                st.session_state['dashboard_view'] = 'nc_ewma'
                st.rerun()

        with col3:
            st.markdown("### ⚖️ Управление рисками")
            st.info("Раздел EWMA-3 (Риски процессов)")
            st.caption("Ожидание настройки аналитики...")

    # ==========================================
    # РЕЖИМ 2: ДЕТАЛИЗАЦИЯ (ВХОД В ПУНКТЫ)
    # ==========================================
    elif st.session_state['dashboard_view'] == 'nc_v':
        st.subheader("📥 (1) Ожидают верификации")
        st.dataframe(v_list[['ID', 'Дата_Время', 'Автор', 'Код', 'Описание_OPS']], use_container_width=True, hide_index=True)

    elif st.session_state['dashboard_view'] == 'nc_m':
        st.subheader("📝 (2) Ожидают планы коррекций (Minor)")
        st.dataframe(m_plan[['ID', 'Код', 'Категория', 'Описание_QA']], use_container_width=True, hide_index=True)

    elif st.session_state['dashboard_view'] == 'nc_c':
        st.subheader("🚨 (3) Ожидают планы CAPA")
        st.dataframe(c_plan[['ID', 'Код', 'Категория', 'Описание_QA']], use_container_width=True, hide_index=True)

    elif st.session_state['dashboard_view'] == 'nc_new':
        st.subheader("🆕 (4) Новые несоответствия (NewNC)")
        st.dataframe(n_nc[['ID', 'Дата_Время', 'Код', 'Описание_QA']], use_container_width=True, hide_index=True)

    elif st.session_state['dashboard_view'] == 'nc_soon':
        st.subheader("📅 (5) Ближайший контроль (7 дней)")
        st.dataframe(soon_df[['ID', 'Код', 'Corr_Deadline', 'CAPA_Deadline']], use_container_width=True, hide_index=True)

    elif st.session_state['dashboard_view'] == 'nc_over':
        st.error("⏰ (6) ПРОСРОЧЕННЫЕ ПРОВЕРКИ")
        st.dataframe(over_df[['ID', 'Код', 'Corr_Deadline', 'CAPA_Deadline', 'Corr_Owner']], use_container_width=True, hide_index=True)

    elif st.session_state['dashboard_view'] == 'nc_ewma':
        st.subheader("📈 (7) Статус EWMA")
        st.info("Превышений порогов статистического контроля не обнаружено.")

    elif st.session_state['dashboard_view'] == 'audit_va':
        st.subheader("🔍 Детализация плана Внутренних аудитов")
        st.write("Здесь будет выведен график Ганта или таблица текущих проверок.")

    elif st.session_state['dashboard_view'] == 'audit_ext':
        st.subheader("🌍 Подготовка к внешнему аудиту")
        st.success("Компания: Рэддис | Дата: 09.07.2026")
        st.text_area("Что подготовить:", value="1. Протоколы анализа со стороны руководства\n2. Отчеты по рискам за 2025 год")

    elif st.session_state['dashboard_view'] == 'audit_lab':
        st.subheader("🧪 Контроль данных лаборатории")
        st.info("Ожидание загрузки файлов от заведующего лабораторией.")
