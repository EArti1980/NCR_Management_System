import streamlit as st
import pandas as pd

def show_minor_management(df, db_file, preselected_id=None):
    st.subheader("📑 Общий реестр несоответствий")
    
    # Фильтры поиска
    with st.expander("🔍 Фильтры поиска и аналитики"):
        col1, col2, col3 = st.columns(3)
        with col1:
            f_process = st.multiselect("Процесс:", options=df['Код'].unique())
        with col2:
            f_cat = st.multiselect("Категория:", options=df['Категория'].unique())
        with col3:
            f_source = st.multiselect("Источник:", options=df['Источник'].unique())
            
    # Применение фильтров
    df_display = df.copy()
    if f_process:
        df_display = df_display[df_display['Код'].isin(f_process)]
    if f_cat:
        df_display = df_display[df_display['Категория'].isin(f_cat)]
    if f_source:
        df_display = df_display[df_display['Источник'].isin(f_source)]

    # СТРОГО ПО ЗАДАЧЕ: Добавляем Описание_OPS, чтобы видеть суть НС
    cols_to_show = [
        'ID', 'Дата_Время', 'Источник', 'Код', 'Автор', 'Должность', 
        'Категория', 'Описание_OPS', 'Описание_QA', 'Статус', 'Corr_Done', 'CAPA_Done'
    ]
    
    # Проверка наличия колонок перед отображением
    existing_cols = [c for c in cols_to_show if c in df_display.columns]
    
    # Форматирование таблицы
    st.dataframe(
        df_display[existing_cols].sort_values('ID', ascending=False),
        use_container_width=True,
        hide_index=True
    )

    # Блок редактирования (если выбрана запись)
    st.write("---")
    st.markdown("### 📝 Детальный просмотр и редактирование")
    
    selected_id = st.number_input("Введите ID для редактирования:", 
                                  min_value=int(df['ID'].min()) if not df.empty else 0,
                                  value=int(preselected_id) if preselected_id else None)
    
    if selected_id:
        row = df[df['ID'] == selected_id]
        if not row.empty:
            row = row.iloc[0]
            st.warning(f"Редактирование НС ID {selected_id}")
            
            with st.form("edit_nc_form"):
                c1, c2 = st.columns(2)
                with c1:
                    new_desc_ops = st.text_area("Описание (Персонал):", value=row['Описание_OPS'])
                    new_cat = st.selectbox("Категория:", ["IntMinor", "IntMajor", "IntCritical", "ExtMinor", "ExtMajor", "ExtCritical"], 
                                           index=["IntMinor", "IntMajor", "IntCritical", "ExtMinor", "ExtMajor", "ExtCritical"].index(row['Категория']))
                with c2:
                    new_desc_qa = st.text_area("Комментарий QA:", value=row['Описание_QA'])
                    new_status = st.selectbox("Статус:", ["Черновик", "На верификации", "Подтверждено", "Отклонено"],
                                              index=["Черновик", "На верификации", "Подтверждено", "Отклонено"].index(row['Статус']))
                
                if st.form_submit_button("Сохранить изменения"):
                    # Логика сохранения в CSV
                    df.loc[df['ID'] == selected_id, 'Описание_OPS'] = new_desc_ops
                    df.loc[df['ID'] == selected_id, 'Описание_QA'] = new_desc_qa
                    df.loc[df['ID'] == selected_id, 'Категория'] = new_cat
                    df.loc[df['ID'] == selected_id, 'Статус'] = new_status
                    df.to_csv(db_file, index=False)
                    st.success("Данные обновлены!")
                    st.rerun()
        else:
            st.error("НС с таким ID не найдено.")
