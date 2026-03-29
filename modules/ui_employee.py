import streamlit as st
import pandas as pd
import os
from datetime import datetime
from config import PROCESSES

def show_employee_interface(db_file, db_cols):
    st.title("📝 Фиксация несоответствия")
    
    # 1. Секция даты и времени
    dt_now = datetime.now().strftime("%d.%m.%Y %H:%M")
    st.caption(f"📅 Дата и время фиксации: {dt_now}")
    
    st.write("---")

    # Проверка наличия данных сотрудника
    if 'u_name' not in st.session_state or not st.session_state['u_name']:
        st.warning("⚠️ Пожалуйста, сначала укажите ваше ФИО и должность в профиле.")
        return

    # --- ИНТЕРАКТИВНЫЙ БЛОК (ВНЕ ФОРМЫ) ---
    # Мы выносим выбор процесса сюда, чтобы страница обновлялась сразу при смене выбора
    
    not_sure = st.checkbox("❓ Не знаю / не уверен, к какому процессу относится НС")
    
    process_options = [f"{k} - {v['full_name']}" for k, v in PROCESSES.items()]
    
    selected_process_full = st.selectbox(
        "1. Код процесса:",
        options=process_options,
        disabled=not_sure,
        help="Выберите наиболее подходящий процесс из списка"
    )

    # ИСПРАВЛЕННАЯ ЛОГИКА ИЗВЛЕЧЕНИЯ КЛЮЧА
    # Теперь мы берем первый элемент списка [0], чтобы получить "УО" или "УРМ"
    selected_key = selected_process_full.split(" - ")[0] if not not_sure else "TBD"
    
    # Получаем данные процесса из config.py
    process_data = PROCESSES.get(selected_key, {})
    hint_text = process_data.get("hint", "Описание областей для данного процесса не заполнено в config.py")

    # Синий блок с подсказками (теперь он обновляется мгновенно)
    if not not_sure:
        st.info(f"🔍 **Области несоответствий для этого кода:**\n\n{hint_text}")
    else:
        st.info("ℹ️ QA-инженер сам определит процесс при верификации.")

    # --- ФОРМА ВВОДА (ДЛЯ ТЕКСТА И ОТПРАВКИ) ---
    with st.form("nc_fixation_form", clear_on_submit=True):
        
        description = st.text_area("2. Описание события (что произошло?):", 
                                  placeholder="Опишите детали инцидента...")
        
        fact_count = st.number_input("3. Количество фактов:", min_value=1, value=1, step=1)

        submit_btn = st.form_submit_button("Отправить в QA на верификацию")

        if submit_btn:
            if not description:
                st.error("Пожалуйста, заполните описание события.")
            else:
                # Определяем итоговый код и название процесса
                final_code = "TBD" if not_sure else selected_key
                final_process = "Определит QA" if not_sure else process_data.get("full_name", "Неизвестно")

                # Загрузка БД
                if os.path.exists(db_file):
                    df = pd.read_csv(db_file)
                else:
                    df = pd.DataFrame(columns=db_cols)

                # Генерация ID
                new_id = int(df['ID'].max() + 1) if not df.empty else 1
                
                # Создание записи
                new_entry = {col: "" for col in db_cols}
                new_entry.update({
                    'ID': new_id,
                    'Дата_Время': dt_now,
                    'Автор': st.session_state['u_name'],
                    'Должность': st.session_state.get('u_job', 'Не указана'),
                    'Код': final_code,
                    'Процесс': final_process,
                    'Описание_OPS': description,
                    'Кол_во': fact_count,
                    'Статус': "На проверке",
                    'Категория': "TBD"
                })

                df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                df.to_csv(db_file, index=False)
                
                st.success(f"✅ Несоответствие ID {new_id} успешно зарегистрировано!")
                st.balloons()

    # Памятка
    with st.expander("ℹ️ Памятка для сотрудника"):
        st.write("""
        *   Описывайте факт, а не догадки.
        *   Указывайте номера оборудования или документов.
        """)
