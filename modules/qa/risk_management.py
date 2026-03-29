import streamlit as st
import pandas as pd
import os
# Исправленный импорт: используем абсолютный путь от корня проекта
from modules.analytics import get_process_risk_rpn
from config import PROCESSES

def show_risk_management(df):
    """
    Интерфейс модуля управления рисками для директора QA.
    Математика и логика полностью вынесены в analytics.py для единства расчетов.
    """
    st.subheader("⚖️ Управление рисками процессов (Модель RPN)")
    
    # Пояснение к модели для пользователя
    with st.expander("ℹ️ Описание модели рисков (S*O*D)"):
        st.write("""
        - **S (Severity):** Тяжесть. Фиксирована на уровне 3.
        - **O (Occurrence):** Вероятность. На основе тренда EWMA (все типы НС).
        - **D (Detection):** Детекция. На основе внешних/аудиторских НС (OPS исключен).
        - **Матрица:** Приоритет отдается детекции (статус 'Внимание' при D=3).
        """)

    risk_results = []
    
    # Собираем данные по всем процессам
    for p_code in PROCESSES.keys():
        # Вызов единой функции расчета из analytics.py
        res = get_process_risk_rpn(df, p_code)
        
        risk_results.append({
            "Код": p_code,
            "Процесс": PROCESSES[p_code]['full_name'],
            "S": 3, 
            "O": res['O'], 
            "D": res['D'],
            "RPN": res['RPN'], 
            "Статус": res['Статус']
        })
    
    # 1. Визуализация карточек (Метрики)
    cols = st.columns(len(risk_results))
    for i, row in enumerate(risk_results):
        with cols[i]:
            # Цветовая индикация согласно статусу
            if row['Статус'] == "СТАБИЛЬНО": 
                m_color = "normal"
            elif row['Статус'] == "ВНИМАНИЕ": 
                m_color = "off"
            else: 
                m_color = "inverse"
            
            st.metric(
                label=row['Код'], 
                value=f"RPN {row['RPN']}", 
                delta=row['Статус'], 
                delta_color=m_color
            )
            
    st.write("---")
    
    # 2. Детальная таблица рисков
    df_risks = pd.DataFrame(risk_results)
    
    # Стилизация таблицы для наглядности
    def highlight_status(val):
        color = 'white'
        if val == 'КРИТИЧЕСКИЙ': color = '#ff4b4b'
        elif val == 'ВНИМАНИЕ': color = '#ffa500'
        elif val == 'СТАБИЛЬНО': color = '#90ee90'
        return f'background-color: {color}; color: black; font-weight: bold'

    st.write("### Сводный реестр рисков")
    # Используем map вместо applymap (для новых версий pandas)
    st.table(df_risks.style.map(highlight_status, subset=['Статус']))

    # 3. Дополнительная информация по логике (для контроля директора)
    if st.checkbox("Показать расшифровку значений O и D"):
        st.info("""
        **Балл 1:** Тренд и текущие значения в пределах нормы (4 Сигмы).
        **Балл 3:** Зафиксировано превышение порога или критический всплеск баллов.
        """)
