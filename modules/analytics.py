import pandas as pd
import os
import numpy as np
from datetime import datetime
from config import PROCESSES, PROBABILITY_SCORES, DETECTION_SCORES

DB_FILE = 'nc_main_data.csv'

def get_nc_analytics(process_code, nc_category):
    """
    Аналитика трендов Minor НС (быстрые датчики). 
    """
    if not os.path.exists(DB_FILE): return pd.DataFrame()
    df = pd.read_csv(DB_FILE)
    
    subset = df[(df['Код'] == process_code) & 
                (df['Категория'] == nc_category) & 
                (df['Статус'] == "Подтверждено")].copy()
                
    if subset.empty: return subset

    params = {
        "IntMinor": {"l": 0.2, "u_coeff": 0.333},
        "ExtMinor": {"l": 0.5, "u_coeff": 0.577}
    }
    
    lmbda, ucl_f = params[nc_category]["l"], params[nc_category]["u_coeff"]

    subset['Date_Obj'] = pd.to_datetime(subset['Дата_Время'], dayfirst=True)
    subset['Month'] = subset['Date_Obj'].dt.to_period('M')
    
    monthly_data = subset.groupby('Month')['Кол_во'].sum().reset_index().sort_values('Month')
    monthly_data['EWMA'] = monthly_data['Кол_во'].ewm(alpha=lmbda, adjust=False).mean()

    avg = monthly_data['Кол_во'].mean()
    std = monthly_data['Кол_во'].std() if len(monthly_data) > 1 else 0.5
    
    monthly_data['UCL'] = avg + (3 * std * ucl_f)
    monthly_data['Alert'] = monthly_data['EWMA'] > monthly_data['UCL']
    monthly_data['Month_Str'] = monthly_data['Month'].astype(str)
    
    return monthly_data

def get_detection_score(source, category):
    """
    Точная логика баллов детекции (PDF стр. 10).
    """
    if source == "OPS": return 0
    
    offset = 0
    if "Major" in category: offset = 1
    if "Critical" in category: offset = 2
    
    base_scores = {
        "IAProc": 4, "IAPrj": 7, "EA": 10, "Ins": 10, "SP/Reg": 10
    }
    
    return base_scores.get(source, 0) + offset

def run_risk_engine(series):
    """
    Математика рисков: Инертная модель (лямбда 0.2, 4 сигмы) 
    + Прямой триггер на критическое событие (балл >= 12).
    """
    if series.empty: return 1
    
    lmbda = 0.2
    k = 4
    
    # Текущее значение месяца (Xi)
    xi = series.iloc[-1]
    
    # 1. ПРАВИЛО КРИТИЧЕСКОГО СОБЫТИЯ (Прямой триггер)
    # Если за месяц набрано 12 и более баллов (прорыв детекции) - сразу риск 3
    if xi >= 12:
        return 3
    
    # 2. МАТЕМАТИКА ТРЕНДА (EWMA)
    ewma_values = series.ewm(alpha=lmbda, adjust=False).mean()
    zi = ewma_values.iloc[-1]
    
    # Расчет порога по скользящему окну 12 месяцев
    window = series.tail(12)
    avg = window.mean()
    std = window.std()
    if pd.isna(std) or std < 2.0:
        std = 2.0 # Предохранитель от нулевого отклонения
        
    ucl = avg + (k * std * 0.333)
    
    # Если инертный тренд накопился и пробил порог
    if zi > ucl:
        return 3
        
    return 1

def get_process_risk_rpn(df, process_code):
    """
    Интегральный расчет RPN (S*O*D).
    """
    S = 3
    p_df = df[(df['Код'] == process_code) & (df['Статус'] == "Подтверждено")].copy()
    
    if p_df.empty:
        return {"RPN": 3, "Статус": "СТАБИЛЬНО", "O": 1, "D": 1}
        
    p_df['Date_Obj'] = pd.to_datetime(p_df['Дата_Время'], dayfirst=True)
    p_df['Month'] = p_df['Date_Obj'].dt.to_period('M')
    
    # Динамический диапазон месяцев от первой до последней записи в базе
    all_months = pd.period_range(start=p_df['Month'].min(), end=p_df['Month'].max(), freq='M')

    # Расчет O (Occurrence)
    p_df['O_Weight'] = p_df['Категория'].map(PROBABILITY_SCORES).fillna(1)
    mo = p_df.groupby('Month')['O_Weight'].sum().reindex(all_months, fill_value=0)
    O = run_risk_engine(mo)

    # Расчет D (Detection)
    p_df['D_Weight'] = p_df.apply(lambda x: get_detection_score(x['Источник'], x['Категория']), axis=1)
    md = p_df.groupby('Month')['D_Weight'].sum().reindex(all_months, fill_value=0)
    D = run_risk_engine(md)

    rpn = S * O * D

    # Логика статусов (Приоритет детекции)
    status = "СТАБИЛЬНО"
    if rpn == 27:
        status = "КРИТИЧЕСКИЙ"
    elif D == 3: 
        status = "ВНИМАНИЕ"
    
    return {"RPN": rpn, "Статус": status, "O": O, "D": D}
