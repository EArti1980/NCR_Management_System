import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# 1. Настройки из СОП и config.py
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

# Все категории согласно вашему запросу
CATS = ["IntMinor", "IntMajor", "IntCritical", "ExtMinor", "ExtMajor", "ExtCritical"]

# Полный список источников НС согласно СОП (п. 2.1)
SOURCES = ["OPS", "IAProc", "IAPrj", "EA", "Ins", "SP/Reg"]

all_rows = []
id_counter = 1
start_date = datetime.now() - timedelta(days=365) # Данные за последний год

for code, full_name in PROCESSES.items():
    # Генерируем по 200 записей на каждый процесс для плотности графиков EWMA
    for i in range(200):
        # Равномерно распределяем даты внутри года
        date = start_date + timedelta(hours=i * 4.3 + random.randint(1, 12))
        
        # Логика распределения критичности (для реалистичности)
        rand = random.random()
        if rand < 0.75: 
            cat = random.choice(["IntMinor", "ExtMinor"])
            source = random.choice(["OPS", "IAProc"]) # Операционка и внутренние аудиты
        elif rand < 0.93:
            cat = random.choice(["IntMajor", "ExtMajor"])
            source = random.choice(["IAPrj", "EA", "Ins"]) # Проекты, внешние аудиты, инспекции
        else:
            cat = random.choice(["IntCritical", "ExtCritical"])
            source = random.choice(["EA", "Ins", "SP/Reg"]) # Регуляторы и критические сбои

        # Моделируем "всплеск" для проверки алертов EWMA (в середине цикла)
        cnt = random.randint(5, 12) if 90 < i < 115 else random.randint(1, 3)

        row = {
            "ID": id_counter,
            "Дата_Время": date.strftime("%d.%m.%Y %H:%M"),
            "Автор": random.choice(["Иванов А.А.", "Петрова Б.В.", "Сидоров Г.Д."]),
            "Код": code,
            "Процесс": full_name,
            "Описание_OPS": f"Первичное описание НС по процессу {code} (факт №{i})",
            "Описание_QA": f"QA: Верифицировано. НС отнесено к {cat}. Требуется мониторинг тренда.",
            "Кол_во": cnt,
            "Источник": source,
            "Категория": cat,
            "Статус": "Подтверждено" if i < 195 else "На проверке"
        }
        all_rows.append(row)
        id_counter += 1

# Сохраняем
df = pd.DataFrame(all_rows)
df.to_csv('nc_main_data.csv', index=False)

print(f"✅ База создана: 1600 записей (8 процессов x 200 НС).")
print(f"📊 Источники: {', '.join(SOURCES)}")
print(f"📈 Категории: {', '.join(CATS)}")
