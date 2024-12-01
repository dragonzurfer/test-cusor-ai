import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

def send_email(sender_email, sender_password, sender_name, recipient_email, subject, body):
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), sender_email))
    msg['To'] = recipient_email

    server = smtplib.SMTP('smtp.zoho.in', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, [recipient_email], msg.as_string())
    server.quit() 

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