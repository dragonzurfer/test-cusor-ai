import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from datetime import datetime, timedelta
import time

def can_send_email(account):
    if not account.last_email_sent:
        return True
    
    time_since_last_email = datetime.now() - account.last_email_sent
    return time_since_last_email >= timedelta(minutes=5)

def send_email(sender_email, sender_password, sender_name, recipient_email, subject, body, account=None, session=None):
    if account and not can_send_email(account):
        wait_time = 5 * 60 - (datetime.now() - account.last_email_sent).total_seconds()
        if wait_time > 0:
            time.sleep(wait_time)
    
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), sender_email))
    msg['To'] = recipient_email

    server = smtplib.SMTP('smtp.zoho.in', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, [recipient_email], msg.as_string())
    server.quit()
    
    if account and session:
        account.last_email_sent = datetime.now()
        session.commit()

def verify_email_credentials(sender_email, sender_password):
    try:
        server = smtplib.SMTP('smtp.zoho.in', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.quit()
        return True
    except Exception as e:
        print(f"Verification failed for {sender_email}: {str(e)}")
        return False 