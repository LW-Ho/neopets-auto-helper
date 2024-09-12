import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class GmailNotify():
    def __init__(self, token: str, sender: str, receiver: str) -> None:
        self._token = token
        self._sender = sender
        self._receiver = receiver

    def notify(self, method: str = '', message: dict = {}) -> bool:
        email_body = json.dumps( \
            message, indent=4, sort_keys=True)

        if not self._token:
            print(f'Gmail notify was disabled {email_body}')
            return False

        if method == 'ok':
            gmail_content = MIMEMultipart()

            gmail_content["subject"] = '[INFO] Running neopets-auto-helper'
            gmail_content["from"] = self._sender
            gmail_content["to"] = self._receiver
            gmail_content.attach(MIMEText(email_body, 'plain'))

            with smtplib.SMTP(host='smtp.gmail.com', port='587') as smtp:
                try:
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.login(self._sender, self._token)
                    print('start sending email')
                    smtp.send_message(gmail_content)
                except Exception as e:
                    print(f"{__name__} error {e}")
                    return False

        elif method == 'error':
            gmail_content = MIMEMultipart()

            gmail_content["subject"] = '[ERROR] Login failed neopets-auto-helper'
            gmail_content["from"] = self._sender
            gmail_content["to"] = self._receiver
            gmail_content.attach(MIMEText(email_body, 'plain'))

            with smtplib.SMTP(host='smtp.gmail.com', port='587') as smtp:
                try:
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.login(self._sender, self._token)
                    print('error sending email')
                    smtp.send_message(gmail_content)
                except Exception as e:
                    print(f"{__name__} error {e}")
                    return False