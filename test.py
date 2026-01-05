from Email_manager import Email_manager
from fastapi import FastAPI, Form, Request, UploadFile, File, BackgroundTasks, HTTPException, status, Depends

email_manager = Email_manager()
name = 'jonny'
email = 'jonnysires@gmail.com'
age = '21'
location = 'CF'
message = 'herro '

# Correct the recipient emails by making it a list or tuple.
emails = ["jonnysires@yahoo.com"]

email_content = email_manager.email_form(name, email, age, location, message)

# Send to site owner(s)
for recipient in emails:
    email_manager.send_email(recipient, email_content, "Contact Form",reply_to_email=email)

# ✅ Auto-reply to user
email_manager.auto_reply_to_form_submitter(email, name)

