import imaplib
import smtplib
import email
from email.message import EmailMessage
import time
import re
import requests

# E-Mail-Konfiguration
IMAP_SERVER = "imap.mail.de"
SMTP_SERVER = "smtp.mail.de"
EMAIL_ADDRESS = "raphaelhauser@mail.de"
PASSWORD = "!Et32cNdzdH9Jz4"

def read_unseen_emails():
    with imaplib.IMAP4_SSL(IMAP_SERVER) as mail:
        mail.login(EMAIL_ADDRESS, PASSWORD)
        mail.select('inbox')

        status, data = mail.search(None, '(UNSEEN)')
        mail_ids = data[0].split()

        emails = []
        for mail_id in mail_ids:
            status, msg_data = mail.fetch(mail_id, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            emails.append(msg)
        return emails

def trigger_flask_endpoint(user_query: str):
    import requests

    endpoint_url = "http://127.0.0.1:5000/chat"

    payload = {"query": user_query}
    try:
        response = requests.post(endpoint_url, json=payload)
        response.raise_for_status()
        result = response.json()
        print(f"Response from Flask endpoint: {result}")
        return result["text"]
    except requests.RequestException as e:
        print(f"Error calling endpoint: {e}")
        return "There was an error contacting the internal service."

def send_email_back(original_email):
    reply = EmailMessage()

    from_address = email.utils.parseaddr(original_email['From'])[1]

    original_subject = original_email.get('Subject', '').replace("\n", "").replace("\r", "")
    subject = "Re: " + original_subject

    # Extract email content safely
    body = ""
    if original_email.is_multipart():
        for part in original_email.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(errors="ignore")
                    break
    else:
        body = original_email.get_payload(decode=True).decode(errors="ignore")

    # Flask-Endpunkt aufrufen, um Antwort zu generieren
    detailed_response = trigger_flask_endpoint(body)

    reply['From'] = EMAIL_ADDRESS
    reply['To'] = from_address
    reply['Subject'] = subject
    reply.set_content(detailed_response)

    with smtplib.SMTP_SSL(SMTP_SERVER, 465) as smtp:
        smtp.login(EMAIL_ADDRESS, PASSWORD)
        smtp.send_message(reply)

def main():
    INTERVAL_SECONDS = 30
    print("Starting email polling...")

    try:
        while True:
            emails = read_unseen_emails()

            if emails:
                print(f"Found {len(emails)} unseen emails.")
                for mail in emails:
                    send_email_back(mail)
                    print(f"Replied to email from {mail['From']}")
            else:
                print("No new emails found.")

            time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("Polling stopped by user.")

if __name__ == "__main__":
    main()
