import smtplib
from email.message import EmailMessage

# Your app credentials
# EMAIL_ADDRESS = "sivadeepkumar3@gmail.com"
# EMAIL_PASSWORD = "mylr mhrm gwni fvbl"  # Use the 16-character App Password

# Create email
msg = EmailMessage()
msg['Subject'] = 'Test Email from Python'
msg['From'] = EMAIL_ADDRESS
msg['To'] = 'sivadeepkumar199@gmail.com'
msg.set_content('This is a test email sent from Python using Gmail SMTP.')

# Send email using Gmail SMTP
with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    smtp.send_message(msg)

print("Email sent successfully!")
