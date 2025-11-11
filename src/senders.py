# src/senders.py
import os
from twilio.rest import Client
import smtplib
from email.message import EmailMessage

def send_sms(body):
    sid = os.getenv("TWILIO_SID")
    auth = os.getenv("TWILIO_AUTH")
    from_num = os.getenv("TWILIO_FROM")
    to_num = os.getenv("PARENT_PHONE")

    if not all([sid, auth, from_num, to_num]):
        print("Twilio not configured; skipping SMS.")
        return

    client = Client(sid, auth)
    print("Sending SMS:", body)
    client.messages.create(body=body, from_=from_num, to=to_num)


def send_email(subject, body, attachment_path=None):
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)
    TO = os.getenv("PARENT_EMAIL")

    if not EMAIL_USER or not EMAIL_PASS:
        print("Email creds missing; skipping email.")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = TO
    msg.set_content(body)

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            data = f.read()
            msg.add_attachment(
                data,
                maintype="audio",
                subtype="wav",
                filename=os.path.basename(attachment_path)
            )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)
    print("Email sent.")
