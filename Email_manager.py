from email.message import EmailMessage
import smtplib
import os
import logging
import mimetypes
from email_config import email_password, email_sender, SMTP_HOST, SMTP_PORT  # Add your new settings here

# Configure logging
logging.basicConfig(
    filename="learnandplaycv.log",
    level=logging.DEBUG,  # Use DEBUG for detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

class Email_manager:
    def __init__(self):
        pass

    def send_email(
        self,
        recipient_emails: str,
        contents: str,
        subject: str,
        reply_to_email: str = None,
        file_data: bytes = None,
        file_name: str = None
    ):
        """Send an email with optional attachment and Reply-To header."""
        try:
            logger.info("Preparing email...")
            em = EmailMessage()
            em["From"] = email_sender
            em["To"] = recipient_emails
            em["Subject"] = subject

            if reply_to_email:
                em["Reply-To"] = reply_to_email

            # Set the plain text content
            em.set_content("This is an email from Learn & Play.")

            # Add the HTML content as an alternative
            em.add_alternative(contents, subtype="html")

            # Attach file if provided
            if file_data and file_name:
                logger.info(f"Attaching file: {file_name}")
                mime_type, _ = mimetypes.guess_type(file_name)
                if mime_type is None:
                    mime_type = "application/octet-stream"
                maintype, subtype = mime_type.split("/", 1)
                em.add_attachment(
                    file_data,
                    maintype=maintype,
                    subtype=subtype,
                    filename=file_name
                )
            logger.info(f"File {file_name} attached successfully.")

            # Connect to Namecheap's SMTP server and send the email
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
                # smtp.set_debuglevel(1)  # Disabled to reduce log verbosity
                smtp.login(email_sender, email_password)
                smtp.send_message(em)
            logger.info("Email sent successfully.")
        except Exception as e:
            logger.error(f"Error while sending email: {e}")

    # The rest of your class (email_form, email_resume, auto_reply_to_form_submitter, etc.) remains unchanged



    def email_form(self, name: str, email: str, age: int, message: str) -> str:
        """Generate email content for a form submission, including a reply button."""

        return f"""<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Email Template</title>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #fff; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }}
                    h1 {{ color: #333; }}
                    p {{ color: #666; }}
                    .button {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #007BFF; color: #fff; text-decoration: none; border-radius: 5px; }}
                    .button:hover {{ background-color: #0056b3; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Form Contents:</h1>
                    <ul>
                        <li>Name: {name}</li>
                        <li>Email: {email}</li>
                        <li>Date Of Birth: {age}</li>
                        <li>Message: {message}</li>
                    </ul>
                </div>
            </body>
            </html>"""


    def email_resume(self, first_name: str, last_name: str, email2: str, phone: str, location: str, experience: str, position: str, additional_info: str = None) -> str:
        """Generate email content for resume submission, including a reply button."""

        return f"""<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Email Template</title>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #fff; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }}
                    h1 {{ color: #333; }}
                    p {{ color: #666; }}
                    .button {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #007BFF; color: #fff; text-decoration: none; border-radius: 5px; }}
                    .button:hover {{ background-color: #0056b3; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Resume Submission:</h1>
                    <ul>
                        <li>First Name: {first_name}</li>
                        <li>Last Name: {last_name}</li>
                        <li>Email: {email2}</li>
                        <li>Phone: {phone}</li>
                        <li>Location: {location}</li>
                        <li>Experience: {experience}</li>
                        <li>Position: {position}</li>
                        <li>Additional Info: {additional_info}</li>
                    </ul>
                </div>
            </body>
            </html>"""

    def auto_reply_to_form_submitter(self, recipient_email: str, recipient_name: str):
        """Send an auto-reply to the person who submitted the form."""
        subject = "Thank You for Contacting Learn & Play Daycare"
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f9f9f9; }}
                .container {{ background: #fff; padding: 20px; border-radius: 8px; max-width: 600px; margin: auto; }}
                h2 {{ color: #333; }}
                p {{ color: #555; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Hello {recipient_name},</h2>
                <p>Thank you for contacting <strong>Learn & Play Daycare</strong>! We have received your message and appreciate your interest.</p>

                <p>Someone from our team will contact you shortly to assist with your inquiry.</p>

                <p>Thank you again for reaching out!</p>
                <p>Warmly,<br>The Learn & Play Team</p>
            </div>
        </body>
        </html>
        """
        self.send_email(recipient_email, html, subject)


    def auto_reply_to_resume_submitter(self, recipient_email: str, first_name: str):
        """Send a thank-you email to the person who submitted a resume."""
        subject = "Thanks for Your Resume Submission"
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f9f9f9; }}
                .container {{ background: #fff; padding: 20px; border-radius: 8px; max-width: 600px; margin: auto; }}
                h2 {{ color: #333; }}
                p {{ color: #555; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Hi {first_name},</h2>
                <p>We’ve received your resume and appreciate your interest in joining Learn & Play.</p>
                <p>Our team will review your submission and reach out if your qualifications match an open opportunity.</p>
                <p>Thank you again!</p>
                <p>Warm regards,<br>The Learn & Play Team</p>
            </div>
        </body>
        </html>
        """
        self.send_email(recipient_email, html, subject)
