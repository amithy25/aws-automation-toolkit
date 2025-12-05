import smtplib
from email.mime.text import MIMEText

# Your credentials
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "amithy25@gmail.com"
sender_password = "ouxy mmjg smaw eeud"  # 16-character app password
recipient_email = "amithy25@gmail.com"  # can be same

# Email content
subject = "Test Email from Python"
body = "Hello! This is a test email using SMTP."

msg = MIMEText(body)
msg["Subject"] = subject
msg["From"] = sender_email
msg["To"] = recipient_email

# Send the email
with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()  # Secure the connection
    server.login(sender_email, sender_password)
    server.send_message(msg)

print("Email sent successfully!")
