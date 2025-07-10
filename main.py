from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from string import Template
import os

load_dotenv()

app = FastAPI()

# Load credentials from .env
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))


def load_email_template(**kwargs) -> str:
    try:
        with open("welcome_email.html", "r", encoding="utf-8") as f:
            content = f.read()
            template = Template(content)
            return template.safe_substitute(**kwargs)
    except Exception as e:
        print("Error loading email template:", e)
        return ""

def send_email(to_email: str, subject: str, html_body: str) -> bool:
    try:
        # Compose email
        message = MIMEMultipart("alternative")
        message["From"] = SMTP_EMAIL
        message["To"] = to_email
        message["Subject"] = subject

        # Add the HTML content to the email
        message.attach(MIMEText(html_body, "html"))

        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(message)
        server.quit()
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False

@app.post("/send-email")
async def send_email_api(
    to_email: str = Form(...),
    subject: str = Form(...),
    user_name: str = Form("User")  # Optional personalization field
):
    # Load and format the HTML template
    html_body = load_email_template(name=user_name)

    if not html_body:
        return JSONResponse(status_code=500, content={"message": "Failed to load email template"})

    success = send_email(to_email, subject, html_body)
    if success:
        return JSONResponse(content={"message": "Email sent successfully"})
    else:
        return JSONResponse(status_code=500, content={"message": "Failed to send email"})
