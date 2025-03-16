import imaplib
import smtplib
import email
from email.message import EmailMessage
import time
import os
import requests

# Secure credentials using environment variables (recommended)
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.mail.de")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.mail.de")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "raphaelhauser@mail.de")
PASSWORD = os.getenv("EMAIL_PASSWORD", "!Et32cNdzdH9Jz4")

# Flask Chatbot API URL
FLASK_ENDPOINT_URL = "http://127.0.0.1:5001/chat"

def read_unseen_emails():
    """Fetch unseen emails from the inbox."""
    with imaplib.IMAP4_SSL(IMAP_SERVER) as mail:
        try:
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
        except Exception as e:
            print(f"Error reading emails: {e}")
            return []

def extract_email_body(msg):
    """Extract text from email (prefers plain text over HTML)."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(errors="ignore")
                    break  # Prefer plain text
    else:
        body = msg.get_payload(decode=True).decode(errors="ignore")

    return body.strip()

def trigger_flask_endpoint(user_query: str):
    """Call the Flask chatbot endpoint with a query and return the response."""
    payload = {"query": user_query}

    try:
        response = requests.post(FLASK_ENDPOINT_URL, json=payload)
        response.raise_for_status()
        result = response.json()

        return result.get("response", "No valid response from AI.")
    except requests.RequestException as e:
        print(f"Error contacting chatbot endpoint: {e}")
        return "There was an error contacting our AI assistant."

def send_email_back(original_email):
    """Send an AI-generated reply to the sender of an email."""
    try:
        reply = EmailMessage()

        from_address = email.utils.parseaddr(original_email['From'])[1]
        original_subject = original_email.get('Subject', '').strip()
        subject = f"Re: {original_subject}" if original_subject else "Re: Your Inquiry"

        # Extract email content
        email_body = extract_email_body(original_email)

        # Generate AI response
        detailed_response = trigger_flask_endpoint(email_body)

        reply['From'] = EMAIL_ADDRESS
        reply['To'] = from_address
        reply['Subject'] = subject
        reply.set_content(detailed_response)

        # Send email
        with smtplib.SMTP_SSL(SMTP_SERVER, 465) as smtp:
            smtp.login(EMAIL_ADDRESS, PASSWORD)
            smtp.send_message(reply)

        print(f"Replied to email from {from_address}")

    except Exception as e:
        print(f"Error sending reply: {e}")

def main():
    """Continuously check for new emails and reply using AI responses."""
    INTERVAL_SECONDS = 10
    print("Starting email polling...")

    try:
        while True:
            emails = read_unseen_emails()

            if emails:
                print(f"Found {len(emails)} unseen emails.")
                for mail in emails:
                    send_email_back(mail)
            else:
                print("No new emails found.")

            time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("Polling stopped by user.")

if __name__ == "__main__":
    main()
