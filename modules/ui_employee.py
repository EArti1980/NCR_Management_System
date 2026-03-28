import streamlit as st
import pandas as pd
from datetime import datetime
from config import PROCESSES
from modules.core import log_audit

def show_employee_interface(db_file, db_cols):
    st.header("📝 Фиксация несоответствия")
    
    # Текущая дата и время
    now_dt = datetime.now()
    now_str = now_dt.strftime("%d.%m.%Y %H:%M")
    st.caption(f"📅 **Дата и время фиксации:** {now_str}")
    
    st.write("---")

    # Контейнер для формы
    with st.container():
        # 1. Чекбокс для тех, кто не знает код процесса
        dont_know = st.checkbox("❓ Не знаю / не уверен, к какому процессу относится НС")

        # 2. Выбор кода процесса (блокируется, если стоит галочка dont_know)
        p_options = list(PROCESSES.keys())
        p_code = st.selectbox(
            "1. Код процесса:", 
            options=p_options, 
            disabled=dont_know,
            format_func=lambda x: f"{x} - {PROCESSES[x].get('full_name', 'Наименование не задано')}",
            help="Выберите процесс из списка или отметьте 'Не знаю', чтобы QA определил его сам."
        )

        # Отображение областей процесса (скрываем, если код не выбран)
        if not dont_know:
            # ИСПОЛЬЗУЕМ .get('areas'), чтобы избежать KeyError, если ключа нет в config.py
            areas_text = PROCESSES[p_code].get('areas', "Описание областей для данного процесса не заполнено в config.py")
            st.info(f"🔍 **Области несоответствий для этого кода:**\n\n{areas_text}")
        else:
            st.warning("⚠️ Код процесса будет определен QA-менеджером при верификации записи.")

        # 3. Описание события
        desc = st.text_area("2. Описание события (что произошло?):", placeholder="Опишите детали инцидента...")

        # 4. Количество фактов
        cnt = st.number_input("3. Количество фактов:", min_value=1, value=1, step=1)

        st.write("---")
        
        # Кнопка отправки
        if st.button("Отправить в QA на верификацию", type="primary"):
            if not desc:
                st.error("❌ Пожалуйста, заполните описание события.")
            else:
                try:
                    # Загружаем БД
                    df = pd.read_csv(db_file)
                    new_id = len(df) + 1
                    
                    # Определяем значения в зависимости от галочки
                    final_code = "TBD" if dont_know else p_code
                    final_process = "Определяется QA" if dont_know else PROCESSES[p_code].get('full_name', 'Неизвестный процесс')
                    
                    # Формируем строку (22 колонки согласно архитектуре)
                    new_row = [
                        new_id, 
                        now_str, 
                        st.session_state.get('u_name', 'Staff_User'), 
                        final_code, 
                        final_process, 
                        desc, 
                        "", # Описание_QA
                        cnt, 
                        "Staff", # Источник
                        "NewNC", # Категория
                        "На проверке" # Статус
                    ]
                    # Добавляем 11 пустых колонок для блоков коррекций и CAPA
                    new_row += [""] * 11
                    
                    # Сохранение
                    new_df = pd.DataFrame([new_row], columns=db_cols)
                    new_df.to_csv(db_file, mode='a', header=False, index=False)
                    
                    # Логирование
                    log_audit(st.session_state.get('u_name', 'Staff_User'), "Регистрация НС", f"ID {new_id} ({final_code})")
                    
                    st.success("✅ Отправлено. Запись появится у QA-менеджера.")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Ошибка при сохранении: {e}")

    # Инструкция внизу страницы
    with st.expander("ℹ️ Памятка для сотрудника"):
        st.write("""
            - Фиксируйте НС сразу после обнаружения.
            - Если вы сомневаетесь в коде процесса, поставьте галочку 'Не знаю' — это не ошибка.
            - Ваше описание должно быть понятным для проведения расследования.
        """)
