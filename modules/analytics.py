import pandas as pd
import numpy as np

def get_nc_analytics(process_code, nc_type):
    """
    Рассчитывает EWMA-тренд для конкретного процесса и типа НС.
    EWMA-1 (IntMinor): lambda=0.2, sigma=2.0
    EWMA-2 (ExtMinor): lambda=0.5, sigma=2.0
    """
    # Загружаем БД
    try:
        df = pd.read_csv('nc_main_data.csv')
    except:
        return None

    # Фильтруем данные по процессу и категории
    df_filtered = df[(df['Код'] == process_code) & (df['Категория'] == nc_type)].copy()
    
    if df_filtered.empty:
        return pd.DataFrame()

    # Агрегируем количество НС по датам
    df_filtered['Дата_Время'] = pd.to_datetime(df_filtered['Дата_Время'], dayfirst=True)
    daily_counts = df_filtered.groupby(df_filtered['Дата_Время'].dt.date).size().reset_index(name='Count')
    daily_counts = daily_counts.sort_values('Дата_Время')

    # Настройки согласно СОП
    lmbda = 0.2 if nc_type == "IntMinor" else 0.5
    sigma_limit = 2.0
    
    # Расчет EWMA
    counts = daily_counts['Count'].values
    ewma_values = []
    z_prev = counts[0] # Начальное значение = первой точке
    
    for x in counts:
        z_curr = lmbda * x + (1 - lmbda) * z_prev
        ewma_values.append(z_curr)
        z_prev = z_curr
        
    daily_counts['EWMA'] = ewma_values
    
    # Расчет контрольных границ (UCL)
    # Упрощенная модель: UCL = Mean + Sigma * Std
    std_val = np.std(counts) if len(counts) > 1 else 0.5
    mean_val = np.mean(counts)
    daily_counts['UCL'] = mean_val + (sigma_limit * std_val)
    
    # Пометка об алерте (превышение порога)
    daily_counts['Alert'] = daily_counts['EWMA'] > daily_counts['UCL']
    
    return daily_counts
