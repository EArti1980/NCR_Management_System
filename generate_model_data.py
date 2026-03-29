import pandas as pd
import os

DB_FILE = 'nc_main_data.csv'

def force_generate_5_months():
    if not os.path.exists(DB_FILE):
        print("Файл базы не найден!")
        return

    df = pd.read_csv(DB_FILE)
    last_id = df['ID'].max()
    
    # Прямое создание 5 месяцев для УРМ (Управление реактивами)
    # Это создаст ряд длиной 5, что больше 3 (условие в коде выполнится)
    data = [
        ('15.11.2025 10:00', 'OPS', 'IntMinor', 1),    # Месяц 1
        ('15.12.2025 10:00', 'OPS', 'IntMinor', 1),    # Месяц 2
        ('15.01.2026 10:00', 'IAProc', 'IntMinor', 1), # Месяц 3 (D=4)
        ('15.02.2026 10:00', 'EA', 'IntMajor', 1),     # Месяц 4 (D=11)
        ('24.03.2026 15:00', 'Ins', 'ExtCritical', 1)  # Месяц 5 (D=12) - Тот самый ID 208
    ]
    
    new_rows = []
    for i, (dt, src, cat, count) in enumerate(data):
        new_rows.append({
            'ID': last_id + 1 + i,
            'Дата_Время': dt,
            'Автор': 'Система_Тест',
            'Должность': 'QA_Бот',
            'Источник': src,
            'Код': 'УРМ',
            'Процесс': 'Управление реактивами, стандартами и т.п.',
            'Описание_OPS': 'Тест EWMA',
            'Описание_QA': 'Техническая проверка',
            'Кол_во': count,
            'Категория': cat,
            'Статус': 'Подтверждено',
            'Correction': 'Да', 'Corr_Owner': 'QA', 'Corr_Deadline': dt, 'Corr_Done': 'Да',
            'CAPA_Plan': '', 'CAPA_Owner': '', 'CAPA_Deadline': '', 'CAPA_Done': 'Нет',
            'CAPA_Effect': '', 'NewNC_Stage': ''
        })
    
    df_final = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    # Удаляем дубликаты по ID на всякий случай
    df_final = df_final.drop_duplicates(subset=['ID'], keep='last')
    df_final.to_csv(DB_FILE, index=False)
    print(f"Добавлено 5 месяцев данных для УРМ. Теперь в базе {len(df_final)} записей.")

if __name__ == "__main__":
    force_generate_5_months()
