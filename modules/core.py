import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from config import EMAIL_CONFIG

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
        import streamlit as st
        st.error(f"❌ Ошибка почтового сервера: {e}")
        return False

def log_audit(user, action, details):
    """Запись в Audit Trail с автоматической архивацией"""
    log_file = 'audit_trail.csv'
    max_rows = 50000
    entry = pd.DataFrame([[datetime.now().strftime("%d.%m.%Y %H:%M:%S"), user, 
                          action, details]], 
                        columns=['Timestamp', 'User', 'Action', 'Details'])
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                row_count = sum(1 for _ in f)
            if row_count >= max_rows:
                ts = datetime.now().strftime("%Y%m%d_%H%M")
                os.rename(log_file, f'audit_trail_archive_{ts}.csv')
        except Exception as e:
            import streamlit as st
            st.error(f"Ошибка ротации логов: {e}")
    entry.to_csv(log_file, mode='a', header=not os.path.exists(log_file), 
                index=False)
