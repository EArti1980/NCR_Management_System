import pandas as pd
import os
from datetime import datetime

DB_FILE = 'nc_main_data.csv'

def get_nc_analytics(process_code, nc_category):
    """Расчет трендов согласно п. 2.4 СОП (стр. 16-17) только для Minor"""
    if nc_category not in ["IntMinor", "ExtMinor"]:
        return pd.DataFrame()
        
    if not os.path.exists(DB_FILE): return pd.DataFrame()
    df = pd.read_csv(DB_FILE)
    
    subset = df[(df['Код'] == process_code) & (df['Категория'] == nc_category) &
                (df['Статус'] == "Подтверждено")].copy()
    
    if subset.empty: return subset

    # Настройки коэффициентов из СОП
    params = {
        "IntMinor": {"l": 0.2, "u": 0.333},
        "ExtMinor": {"l": 0.5, "u": 0.577}
    }
    lmbda = params[nc_category]["l"]
    ucl_c = params[nc_category]["u"]

    subset['Дата_объект'] = pd.to_datetime(subset['Дата_Время'], dayfirst=True)
    subset = subset.sort_values('Дата_объект')

    subset['EWMA'] = subset['Кол_во'].ewm(alpha=lmbda, adjust=False).mean()
    avg = subset['Кол_во'].mean()
    std = subset['Кол_во'].std() if len(subset) > 1 else 0.5
    subset['UCL'] = avg + (2 * std * ucl_c)
    subset['Alert'] = subset['EWMA'] > subset['UCL']
    
    return subset
