import pandas as pd
import random
import os
from datetime import datetime, timedelta

DB_FILE = 'nc_main_data.csv'

def restore_database_300():
    processes = {
        "УО": "Управление оборудованием", "УКС": "Управление компьютеризированными системами",
        "УДЗ": "Управление документами и записями", "УРМ": "Управление реактивами, стандартами и т.п.",
        "УП": "Управление помещениями", "УПс": "Управление персоналом",
        "УПП": "Управление поставками", "ПР": "Проектная деятельность"
    }
    
    rows = []
    current_id = 1
    
    # 1. ГЕНЕРАЦИЯ ФОНА (200 записей по всем процессам)
    start_date = datetime(2025, 4, 1)
    for _ in range(200):
        p_code = random.choice(list(processes.keys()))
        cat = random.choices(["IntMinor", "IntMajor", "ExtMinor"], weights=[80, 15, 5])[0]
        src = "OPS" if "Int" in cat else "EA"
        
        days_offset = random.randint(0, 360)
        dt = (start_date + timedelta(days=days_offset)).strftime('%d.%m.%Y %H:%M')
        
        rows.append({
            'ID': current_id, 'Дата_Время': dt, 'Автор': 'Иванов И.И.', 'Должность': 'Оператор',
            'Источник': src, 'Код': p_code, 'Процесс': processes[p_code],
            'Описание_OPS': 'Плановая запись', 'Описание_QA': 'Подтверждено QA',
            'Кол_во': 1, 'Категория': cat, 'Статус': 'Подтверждено',
            'Correction': 'Да', 'Corr_Owner': 'QA', 'Corr_Deadline': dt, 'Corr_Done': 'Да',
            'CAPA_Plan': '', 'CAPA_Owner': '', 'CAPA_Deadline': '', 'CAPA_Done': 'Нет',
            'CAPA_Effect': '', 'NewNC_Stage': ''
        })
        current_id += 1

    # 2. МОДЕЛЬ УРМ (100 записей за 5 месяцев: Ноябрь - Март)
    # По 20 записей на каждый месяц
    urm_schedule = [
        {"month": 11, "year": 2025, "ext_nc": None},
        {"month": 12, "year": 2025, "ext_nc": None},
        {"month": 1, "year": 2026, "ext_nc": ("IAProc", "IntMinor")}, # Январь (D=4)
        {"month": 2, "year": 2026, "ext_nc": ("EA", "IntMajor")},     # Февраль (D=11)
        {"month": 3, "year": 2026, "ext_nc": ("Ins", "ExtCritical")}  # Март (D=12)
    ]

    for period in urm_schedule:
        for i in range(20):
            # В каждом месяце 19 записей OPS и 1 внешняя (если указана)
            if i == 19 and period["ext_nc"]:
                src, cat = period["ext_nc"]
            else:
                src, cat = "OPS", "IntMinor"
                
            dt = f"{random.randint(1,28):02d}.{period['month']:02d}.{period['year']} {random.randint(9,17):02d}:00"
            
            rows.append({
                'ID': current_id, 'Дата_Время': dt, 'Автор': 'Система_Тест', 'Должность': 'QA_Бот',
                'Источник': src, 'Код': 'УРМ', 'Процесс': processes['УРМ'],
                'Описание_OPS': f'Модель УРМ (Месяц {period["month"]})', 'Описание_QA': 'Контроль инерции',
                'Кол_во': 1, 'Категория': cat, 'Статус': 'Подтверждено',
                'Correction': 'Да', 'Corr_Owner': 'QA', 'Corr_Deadline': dt, 'Corr_Done': 'Да',
                'CAPA_Plan': '', 'CAPA_Owner': '', 'CAPA_Deadline': '', 'CAPA_Done': 'Нет',
                'CAPA_Effect': '', 'NewNC_Stage': ''
            })
            current_id += 1

    df_final = pd.DataFrame(rows)
    # Сортировка по дате для красоты реестра
    df_final['temp_date'] = pd.to_datetime(df_final['Дата_Время'], dayfirst=True)
    df_final = df_final.sort_values('temp_date').drop('temp_date', axis=1)
    
    df_final.to_csv(DB_FILE, index=False)
    print(f"База воссоздана: 300 записей. Процесс УРМ усилен (100 НС за 5 мес).")

if __name__ == "__main__":
    restore_database_300()
