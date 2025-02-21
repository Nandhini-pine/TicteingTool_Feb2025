import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email details
from_email = "wwdsupport_noreply@titan.co.in"
to_email = "goutam_sg@titan.co.in"
subject = "Test Mail from Titan Server"
body = """
<p>Dear Nandhini,</p>
<p>This is a test email sent from the Titan mail server.</p>
<p>Best Regards,<br>Support Team</p>
"""

# Create the email message
message = MIMEMultipart()
message['From'] = from_email
message['To'] = to_email
message['Subject'] = subject
message.attach(MIMEText(body, 'html'))

# SMTP server configuration
smtp_server = 'titan-co-in.mail.protection.outlook.com'
smtp_port = 25  # Change to 587 for TLS

# Send the email using TLS
try:
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Start TLS for encryption
        # If needed, you can add login here if authentication is required
        # server.login('your_email', 'your_password')
        server.sendmail(from_email, to_email, message.as_string())
        print("Mail sent successfully.")
except Exception as e:
    print(f"Failed to send email: {e}")
