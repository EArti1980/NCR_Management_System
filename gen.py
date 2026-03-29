import pandas as pd
import random
from datetime import datetime, timedelta

# 1. Настройки (соответствуют вашему config.py)
PROCESSES = {
    "УО": "Управление оборудованием",
    "УКС": "Управление компьютеризированными системами",
    "УДЗ": "Управление документами и записями",
    "УРМ": "Управление реактивами, стандартами и т.п.",
    "УП": "Управление помещениями",
    "УПс": "Управление персоналом",
    "УПП": "Управление поставками",
    "ПР": "Проектная деятельность"
}

DB_COLS = [
    'ID', 'Дата_Время', 'Автор', 'Код', 'Процесс', 'Описание_OPS', 'Описание_QA', 
    'Кол_во', 'Источник', 'Категория', 'Статус',
    'Correction', 'Corr_Deadline', 'Corr_Owner', 'Corr_Done',
    'Root_Cause', 'CAPA_Plan', 'CAPA_Deadline', 'CAPA_Owner', 'CAPA_Done',
    'QA_Comment', 'Is_Recurrent'
]

all_rows = []
id_counter = 1
start_date = datetime.now() - timedelta(days=365)

for code, full_name in PROCESSES.items():
    for i in range(200):
        # Распределяем записи по году
        date_obj = start_date + timedelta(hours=i * 4.3 + random.randint(1, 12))
        
        # Логика критичности
        rand = random.random()
        if rand < 0.80:
            cat = random.choice(["IntMinor", "ExtMinor"])
            source = random.choice(["OPS", "IAProc"])
        elif rand < 0.95:
            cat = random.choice(["IntMajor", "ExtMajor"])
            source = random.choice(["IAPrj", "EA", "Ins"])
        else:
            cat = random.choice(["IntCritical", "ExtCritical"])
            source = random.choice(["EA", "Ins", "SP/Reg"])

        # Моделируем "всплеск" для EWMA в середине года
        is_spike = (100 < i < 130)
        cnt = random.randint(8, 15) if is_spike else random.randint(1, 3)

        # Статус: последние записи оставим "На проверке" для Дашборда
        status = "На проверке" if i > 195 else "Подтверждено"
        
        # Дедлайны (для пунктов 5 и 6 Дашборда)
        # Сделаем несколько записей просроченными (старые даты)
        corr_done = "Да" if i < 180 else "Нет"
        deadline = (date_obj + timedelta(days=7)).strftime("%d.%m.%Y") if i > 170 else "01.01.2024"

        row = {
            "ID": id_counter,
            "Дата_Время": date_obj.strftime("%d.%m.%Y %H:%M"),
            "Автор": random.choice(["Иванов А.А.", "Петрова Б.В.", "Сидоров Г.Д."]),
            "Код": code,
            "Процесс": full_name,
            "Описание_OPS": f"Авто-генерация: обнаружен дефект в блоке {code} (инцидент {i})",
            "Описание_QA": f"Верифицировано QA. Риск оценен как {cat}.",
            "Кол_во": cnt,
            "Источник": source,
            "Категория": cat,
            "Статус": status,
            "Correction": "Проведена оперативная коррекция" if status == "Подтверждено" else "",
            "Corr_Deadline": deadline if status == "Подтверждено" else "",
            "Corr_Owner": "Тех. отдел",
            "Corr_Done": corr_done,
            "Root_Cause": "Человеческий фактор" if "Major" in cat else "",
            "CAPA_Plan": "Внеплановое обучение" if "Major" in cat else "",
            "CAPA_Deadline": deadline if "Major" in cat else "",
            "CAPA_Owner": "QA менеджер",
            "CAPA_Done": "Нет",
            "QA_Comment": "Проверка эффективности запланирована",
            "Is_Recurrent": "Нет"
        }
        all_rows.append(row)
        id_counter += 1

df = pd.DataFrame(all_rows, columns=DB_COLS)
df.to_csv('nc_main_data.csv', index=False)
print(f"✅ База на 1600 записей успешно создана в файле nc_main_data.csv")
