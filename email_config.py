import os
from dotenv import load_dotenv

load_dotenv()

email_sender = os.getenv("EMAIL_SENDER", "no-reply@learnandplaycv.com")
email_password = os.getenv("EMAIL_PASSWORD", "")

SMTP_HOST = os.getenv("SMTP_HOST", "mail.privateemail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
