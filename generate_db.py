import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta
# Импортируем настройки из вашего config.py
from config import PROCESSES, SOURCES, DB_COLS

def generate_fake_db(num_records=200):
    data = []
    # Генерируем данные за последний год (с марта 2025 по март 2026)
    start_date = datetime.now() - timedelta(days=365)
    
    # Списки для генерации на основе вашего config.py
    process_codes = list(PROCESSES.keys())
    source_codes = list(SOURCES.keys())
    
    # Категории с весами (80% Minor, остальные по убыванию частоты)
    categories = ["IntMinor", "IntMajor", "IntCritical", "ExtMinor", "ExtMajor", "ExtCritical"]
    cat_weights = [0.80, 0.10, 0.04, 0.03, 0.02, 0.01]

    authors = ["Иванов И.И.", "Петров П.П.", "Сидорова С.А.", "Кузнецов В.М."]
    jobs = ["Оператор", "Лаборант", "Инженер", "Мастер смены"]

    for i in range(1, num_records + 1):
        # 1. Дата и время (равномерно по году)
        days_offset = random.randint(0, 365)
        seconds_offset = random.randint(0, 86400)
        dt = start_date + timedelta(days=days_offset, seconds=seconds_offset)
        dt_str = dt.strftime("%d.%m.%Y %H:%M")
        
        # 2. Выбор параметров из конфига
        author = random.choice(authors)
        job = random.choice(jobs)
        p_code = random.choice(process_codes)
        source = random.choice(source_codes)
        category = np.random.choice(categories, p=cat_weights)
        
        # 3. Формирование описаний
        desc_ops = f"Выявлено отклонение в процессе {p_code}, источник: {SOURCES[source]}."
        desc_qa = f"Техническое подтверждение инцидента. Требуется анализ первопричин."
        
        # 4. Логика мероприятий
        is_minor = "Minor" in category
        corr_done = "Да" if is_minor else random.choice(["Да", "Нет"])
        
        capa_plan = ""
        capa_done = "Нет"
        if not is_minor:
            capa_plan = "Провести корневой анализ причин и актуализировать инструкции."
            capa_done = random.choice(["Да", "Нет"])

        # 5. Сборка строки (строго по DB_COLS из вашего config.py)
        # ИСПРАВЛЕНО: Убран оператор :=, который вызывал ошибку 1, U
        row = {col: "" for col in DB_COLS}
        row.update({
            'ID': i,
            'Дата_Время': dt_str,
            'Автор': author,
            'Должность': job,
            'Источник': source,
            'Код': p_code,
            'Процесс': PROCESSES[p_code]['full_name'],
            'Описание_OPS': desc_ops,
            'Описание_QA': desc_qa,
            'Кол_во': random.randint(1, 5),
            'Категория': category,
            'Статус': "Подтверждено",
            'Correction': "Выполнена коррекция" if is_minor else "План коррекции",
            'Corr_Owner': "Начальник отдела",
            'Corr_Deadline': (dt + timedelta(days=7)).strftime("%d.%m.%Y"),
            'Corr_Done': corr_done,
            'CAPA_Plan': capa_plan,
            'CAPA_Owner': "QA-инженер" if capa_plan else "",
            'CAPA_Deadline': (dt + timedelta(days=30)).strftime("%d.%m.%Y") if capa_plan else "",
            'CAPA_Done': capa_done,
            'CAPA_Effect': "Эффективно" if capa_done == "Да" else "",
            'NewNC_Stage': ""
        })
        data.append(row)

    # Сохранение базы данных
    df = pd.DataFrame(data)
    df.to_csv('nc_main_data.csv', index=False)
    
    print(f"--- ГЕНЕРАЦИЯ ЗАВЕРШЕНА ---")
    print(f"Файл 'nc_main_data.csv' успешно создан.")
    print(f"Количество записей: {num_records}")

if __name__ == "__main__":
    generate_fake_db(200)
