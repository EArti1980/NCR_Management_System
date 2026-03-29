import streamlit as st
import pandas as pd
import os
import smtplib
import random
import string
from email.mime.text import MIMEText
from datetime import datetime
# Импортируем настройки из вашего config.py
from config import PROCESSES, PROBABILITY_SCORES, DETECTION_SCORES, EMAIL_CONFIG

# --- 1. СЕРВИСНЫЕ ФУНКЦИИ (БЕЗОПАСНОСТЬ И СВЯЗЬ) ---
def send_email(receiver_email, subject, body):
    """Отправка уведомлений согласно настройкам в config.py"""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_CONFIG['sender_email']
    msg['To'] = receiver_email
    try:
        server = smtplib.SMTP_SSL(EMAIL_CONFIG['smtp_server'], 
                                EMAIL_CONFIG['smtp_port'], timeout=15)
        server.login(EMAIL_CONFIG['sender_email'], 
                     EMAIL_CONFIG['sender_password'])
        server.sendmail(EMAIL_CONFIG['sender_email'], receiver_email, 
                        msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"❌ Ошибка почтового сервера: {e}")
        return False

def log_audit(user, action, details):
    """Запись в Audit Trail с автоматической архивацией при 50 000 строк"""
    log_file = 'audit_trail.csv'
    max_rows = 50000
    # Формируем новую запись
    entry = pd.DataFrame([[datetime.now().strftime("%d.%m.%Y %H:%M:%S"), user, 
                          action, details]], 
                        columns=['Timestamp', 'User', 'Action', 'Details'])
    if os.path.exists(log_file):
        try:
            # Считаем строки без загрузки файла в память
            with open(log_file, 'r', encoding='utf-8') as f:
                row_count = sum(1 for _ in f)
            # Если лимит превышен — создаем архив с таймстампом
            if row_count >= max_rows:
                ts = datetime.now().strftime("%Y%m%d_%H%M")
                archive_name = f'audit_trail_archive_{ts}.csv'
                os.rename(log_file, archive_name)
        except Exception as e:
            st.error(f"Ошибка ротации логов: {e}")
    # Записываем данные (создаст новый файл, если старый ушел в архив)
    entry.to_csv(log_file, mode='a', header=not os.path.exists(log_file), 
                index=False)

# --- 2. ИНИЦИАЛИЗАЦИЯ БАЗ ДАННЫХ ---
DB_FILE = 'nc_main_data.csv'
# Структура колонок: ID, Дата, Автор, Код, Название, Описание_Персонал, 
# Описание_QA, Кол-во, Источник, Категория, Статус
DB_COLS = [
    'ID', 'Дата_Время', 'Автор', 'Код', 'Процесс', 
    'Описание_OPS', 'Описание_QA', 'Кол_во', 
    'Источник', 'Категория', 'Статус'
]

if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=DB_COLS).to_csv(DB_FILE, index=False)

if 'auth' not in st.session_state:
    st.session_state['auth'] = False

# --- 3. МАТЕМАТИЧЕСКИЙ БЛОК (EWMA-1 И EWMA-2 ДЛЯ Minor НС) ---
def get_nc_analytics(process_code, nc_category):
    """Расчет трендов согласно п. 2.4 СОП (стр. 16-17)"""
    # Добавлено ограничение: EWMA только для Minor
    if nc_category not in ["IntMinor", "ExtMinor"]:
        return pd.DataFrame()

    if not os.path.exists(DB_FILE): return pd.DataFrame()
    df = pd.read_csv(DB_FILE)
    
    # Фильтр: только подтвержденные записи конкретного процесса и типа Minor
    subset = df[(df['Код'] == process_code) & (df['Категория'] == nc_category) &
                (df['Статус'] == "Подтверждено")].copy()
    
    if subset.empty: return subset

    # Коэффициенты из СОП: IntMinor (λ=0.2, UCL_c=0.333) | ExtMinor (λ=0.5, UCL_c=0.577)
    params = {
        "IntMinor": {"l": 0.2, "u": 0.333},
        "ExtMinor": {"l": 0.5, "u": 0.577}
    }
    lmbda = params[nc_category]["l"]
    ucl_c = params[nc_category]["u"]

    # Добавлена сортировка для корректного расчета скользящего среднего
    subset['Дата_объект'] = pd.to_datetime(subset['Дата_Время'], dayfirst=True)
    subset = subset.sort_values('Дата_объект')

    # Расчет EWMA
    subset['EWMA'] = subset['Кол_во'].ewm(alpha=lmbda, adjust=False).mean()
    
    # Расчет динамического порога (UCL)
    avg = subset['Кол_во'].mean()
    std = subset['Кол_во'].std() if len(subset) > 1 else 0.5
    subset['UCL'] = avg + (2 * std * ucl_c) #
    
    # Флаг алерта для визуализации
    subset['Alert'] = subset['EWMA'] > subset['UCL']
    
    return subset

# --- 4. БЛОК АВТОРИЗАЦИИ И РЕГИСТРАЦИИ ---
if not st.session_state['auth']:
    st.title("🔐 Система управления НС - Вход")
    mode = st.radio("Выберите действие:", ["Вход", "Регистрация", "Забыли пароль?"]) #

    if mode == "Регистрация":
        with st.form("reg_form"):
            fio = st.text_input("ФИО полностью")
            email = st.text_input("Корпоративный Email")
            u_role = st.selectbox("Ваша роль", ["Сотрудник", "QA Менеджер", "Admin"])
            if st.form_submit_button("Запросить доступ"):
                if fio and email:
                    users = pd.read_csv('users.csv') if os.path.exists('users.csv') else pd.DataFrame(columns=['name','email','password','role'])
                    if email in users['email'].values:
                        st.error("Пользователь с таким email уже существует")
                    else:
                        temp_pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                        if send_email(email, "Доступ к системе НС", f"Ваш пароль для входа: {temp_pwd}"):
                            new_u = pd.DataFrame([[fio, email, temp_pwd, u_role]], columns=['name','email','password','role']) #
                            new_u.to_csv('users.csv', mode='a', header=not os.path.exists('users.csv'), index=False)
                            st.success(f"✅ Пароль отправлен на {email}")
                            log_audit("Система", "Регистрация", email)

    elif mode == "Забыли пароль?":
        with st.form("forgot"):
            email_res = st.text_input("Введите Email для восстановления")
            if st.form_submit_button("Выслать пароль"):
                if os.path.exists('users.csv'):
                    users = pd.read_csv('users.csv')
                    u_data = users[users['email'] == email_res]
                    if not u_data.empty:
                        # Восстановлен оригинальный синтаксис
                        send_email(email_res, "Восстановление доступа", f"Ваш пароль: {u_data.iloc[0]['password']}")
                        st.success("Инструкции отправлены на почту.")
                    else: st.error("Email не найден в базе")

    else:
        with st.form("login_form"): #
            le = st.text_input("Email")
            lp = st.text_input("Пароль", type="password")
            if st.form_submit_button("Войти в систему"):
                if os.path.exists('users.csv'):
                    users = pd.read_csv('users.csv')
                    valid = users[(users['email'] == le) & (users['password'] == lp)]
                    if not valid.empty:
                        # Восстановлен оригинальный синтаксис
                        st.session_state.update({
                            'auth': True,
                            'u_name': valid.iloc[0]['name'],
                            'u_role': valid.iloc[0]['role'],
                            'active_role': valid.iloc[0]['role']
                        })
                        log_audit(st.session_state['u_name'], "Вход", "Успешно")
                        st.rerun()
                    else: st.error("Неверный логин или пароль")
    st.stop()

# --- 5. БОКОВАЯ ПАНЕЛЬ (SIDEBAR) ---
st.sidebar.success(f"👤 {st.session_state['u_name']}")
# Функционал для роли Admin
if st.session_state['u_role'] == "Admin":
    st.sidebar.warning("🛠️ АДМИН-ПАНЕЛЬ ТЕСТИРОВАНИЯ")
    test_role = st.sidebar.radio("Переключить интерфейс на:", ["Сотрудник", "QA Менеджер"])
    st.session_state['active_role'] = test_role
    st.sidebar.info(f"🎭 Активный доступ: {st.session_state['active_role']}")

# Визуализация EWMA в сайдбаре
if st.sidebar.checkbox("📊 Показать графики трендов"):
    p_an = st.sidebar.selectbox("Выберите процесс:", list(PROCESSES.keys()))
    st.sidebar.markdown(f"**Подсказка (Область НС):**\n*{PROCESSES[p_an]['hint']}*")
    
    for c_type in ["IntMinor", "ExtMinor"]:
        data_plot = get_nc_analytics(p_an, c_type)
        if not data_plot.empty:
            # Индикация алерта в заголовке
            is_alert = data_plot.iloc[-1]['Alert']
            st.sidebar.write(f"{'🔴 ALERT' if is_alert else '📈'} **{c_type}**")
            st.sidebar.line_chart(data_plot, x='Дата_Время', y=['EWMA', 'UCL'])
        else:
            st.sidebar.caption(f"Нет данных по {c_type}")

if st.sidebar.button("Выйти из системы"):
    st.session_state['auth'] = False
    st.rerun()

now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

# --- 6. ЛОГИКА ИНТЕРФЕЙСОВ ---
# --- А. ИНТЕРФЕЙС СОТРУДНИКА (Первичный ввод) ---
if st.session_state['active_role'] == "Сотрудник":
    st.header("📝 Регистрация первичного события (Персонал)")
    with st.form("ops_form"):
        p_code = st.selectbox("1. Код процесса:", list(PROCESSES.keys()), 
                            format_func=lambda x: f"{x} - {PROCESSES[x]['full_name']}")
        st.info(f"🔍 **Области несоответствий для этого кода:**\n\n{PROCESSES[p_code]['hint']}")
        desc_ops = st.text_area("2. Описание события (что произошло?):")
        cnt = st.number_input("3. Количество фактов:", min_value=1, value=1)
        if st.form_submit_button("Отправить в QA на верификацию"):
            if desc_ops:
                df = pd.read_csv(DB_FILE)
                new_id = len(df) + 1
                new_row = [
                    new_id, now_str, st.session_state['u_name'], p_code, 
                    PROCESSES[p_code]['full_name'], desc_ops, "", cnt, 
                    "OPS", "ОЖИДАЕТ", "На проверке"
                ]
                pd.DataFrame([new_row], columns=DB_COLS).to_csv(DB_FILE, 
                            mode='a', header=False, index=False)
                log_audit(st.session_state['u_name'], "Создание черновика НС", 
                         f"ID {new_id}")
                st.success("✅ Отправлено. Запись появится у QA-менеджера.")

# --- Б. ИНТЕРФЕЙС QA МЕНЕДЖЕРА ---
else:
    st.header("🛡️ Управление качеством (QA)")
    t1, t2, t3 = st.tabs(["🔍 Верификация черновиков", 
                         "➕ Прямой ввод (QA/Аудит)", "📄 Весь Реестр"])
    
    with t1:
        df = pd.read_csv(DB_FILE)
        pending = df[df['Статус'] == "На проверке"]
        if not pending.empty:
            sid = st.selectbox("Выберите ID записи для проверки:", pending['ID'])
            # Восстановлен оригинальный синтаксис
            row = pending[pending['ID'] == sid].iloc[0]
            st.warning(f"📌 **Черновик от {row['Автор']}**")
            st.write(f"**Оригинал описания:** {row['Описание_OPS']}")
            st.caption(f"ℹ️ Справочно (Область НС): {PROCESSES[row['Код']]['hint']}")
            with st.form("qa_verify_form"): #
                n_desc = st.text_area("Техническое описание (QA):", value=row['Описание_OPS'])
                n_cnt = st.number_input("Уточненное количество:", 
                                      value=int(row['Кол_во']), min_value=1) #
                cat = st.selectbox("Присвоить категорию:", 
                                 ["IntMinor", "IntMajor", "IntCritical", 
                                  "ExtMinor", "ExtMajor", "ExtCritical", "NewNC"])
                if st.form_submit_button("Утвердить и внести в аналитику"):
                    df.loc[df['ID'] == sid, 
                           ['Описание_QA', 'Кол_во', 'Категория', 'Статус']] = \
                    [n_desc, n_cnt, cat, "Подтверждено"]
                    df.to_csv(DB_FILE, index=False)
                    log_audit(st.session_state['u_name'], "Верификация НС", 
                             f"ID {sid} -> {cat}")
                    if "Major" in cat or "Critical" in cat:
                        st.error(f"🚨 ВНИМАНИЕ: Для {cat} необходимо CAPA!")
                    st.success("✅ Запись подтверждена.")
                    st.rerun()
        else: st.write("Нет новых записей для верификации.")

    with t2: #
        st.subheader("Прямое внесение данных (Внешние источники / Аудиты)")
        with st.form("qa_direct_form"):
            d_src = st.selectbox("Источник обнаружения:", 
                               ["IAProc", "IAPrj", "EA", "Ins", "SP/Reg"])
            d_code = st.selectbox("Код процесса:", list(PROCESSES.keys()), 
                                format_func=lambda x: f"{x} - {PROCESSES[x]['full_name']}")
            st.info(f"🔍 **Область:** {PROCESSES[d_code]['hint']}")
            d_cat = st.selectbox("Категория НС:", ["IntMinor", "IntMajor", 
                                                 "IntCritical", "ExtMinor", 
                                                 "ExtMajor", "ExtCritical", "NewNC"])
            d_desc = st.text_area("Техническое описание")
            d_cnt = st.number_input("Кол-во фактов:", min_value=1, value=1)
            if st.form_submit_button("Внести напрямую в реестр"):
                df = pd.read_csv(DB_FILE)
                new_row = [len(df)+1, now_str, st.session_state['u_name'], 
                          d_code, PROCESSES[d_code]['full_name'], d_desc, 
                          d_desc, d_cnt, d_src, d_cat, "Подтверждено"]
                pd.DataFrame([new_row], columns=DB_COLS).to_csv(DB_FILE, 
                            mode='a', header=False, index=False)
                log_audit(st.session_state['u_name'], "Прямой ввод", d_cat)
                st.success("✅ Запись внесена.")
                st.rerun()
                
    with t3: #
        st.subheader("Полный реестр подтвержденных НС")
        df_all = pd.read_csv(DB_FILE)
        st.dataframe(df_all[df_all['Статус'] == "Подтверждено"]) #

# --- 7. БЛОК AUDIT TRAIL (Доступен только QA и Админу) ---
if st.session_state['active_role'] != "Сотрудник":
    st.write("---")
    with st.expander("🛠️ Управление логами (Audit Trail)"):
        if os.path.exists('audit_trail.csv'):
            audit_df = pd.read_csv('audit_trail.csv')
            col_l, col_r = st.columns(2)
            with col_l:
                show_all = st.checkbox("Показать весь лог")
            with col_r:
                limit = st.number_input("Кол-во строк:", min_value=1, 
                                      value=20, disabled=show_all)
            st.dataframe(audit_df if show_all else audit_df.tail(limit), 
                        use_container_width=True)
            # Восстановлена оригинальная кнопка скачивания
            st.download_button(
                label="📥 Скачать полный Audit Trail (.csv)",
                data=audit_df.to_csv(index=False).encode('utf-8'),
                file_name=f"audit_trail_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("Журнал аудита пока пуст.")
