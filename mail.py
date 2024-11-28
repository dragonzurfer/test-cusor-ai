import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import os

# Define to/from
sender = 'ahana@chicfit.in'
sender_title = "Ahana"
recipient = 'ahana@blackburnmedia.in'

# Create message
msg = MIMEText("Message text", 'plain', 'utf-8')
msg['Subject'] = Header("Sent from python", 'utf-8')
msg['From'] = formataddr((str(Header(sender_title, 'utf-8')), sender))
msg['To'] = recipient

# Create server object and start TLS
server = smtplib.SMTP('smtp.zoho.in', 587)
server.ehlo()
server.starttls()
server.ehlo()

# Enable debugging (optional)
server.set_debuglevel(1)

# Perform operations via server
email = os.getenv('ZOHO_EMAIL')
password = os.getenv('ZOHO_APP_PASSWORD')  # Use app-specific password if 2FA is enabled
server.login(email, password)
server.sendmail(sender, [recipient], msg.as_string())
server.quit()