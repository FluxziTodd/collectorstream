"""
Email service for CollectorStream contact and feedback forms
Uses Postmark for reliable email delivery
"""

import httpx
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.api_key = "3b1bc9be-2a11-4e78-ad3f-04790b22c368"
        self.api_url = "https://api.postmarkapp.com/email"
        self.from_email = "todd@fluxzi.com"
        self.to_email = "todd@fluxzi.com"

    def send_contact_email(
        self,
        name: str,
        email: str,
        subject: str,
        message: str
    ) -> bool:
        """Send contact form submission via email"""
        try:
            email_subject = f"CollectorStream Contact: {subject}"
            email_body = f"""New contact form submission from CollectorStream:

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}

---
Reply to: {email}
"""

            response = httpx.post(
                self.api_url,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "X-Postmark-Server-Token": self.api_key
                },
                json={
                    "From": self.from_email,
                    "To": self.to_email,
                    "Subject": email_subject,
                    "TextBody": email_body,
                    "ReplyTo": email,
                    "MessageStream": "outbound"
                },
                timeout=10.0
            )

            if response.status_code == 200:
                logger.info(f"Contact email sent successfully via Postmark")
                return True
            else:
                logger.error(f"Postmark error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send contact email: {e}")
            return False

    def send_feedback_email(
        self,
        feedback_type: str,
        feedback: str,
        email: Optional[str] = None
    ) -> bool:
        """Send feedback form submission via email"""
        try:
            email_subject = f"CollectorStream Feedback: {feedback_type}"
            email_body = f"""New feedback submission from CollectorStream:

Type: {feedback_type}
User Email: {email or 'Not provided'}

Feedback:
{feedback}

---
"""
            if email:
                email_body += f"Reply to: {email}"

            payload = {
                "From": self.from_email,
                "To": self.to_email,
                "Subject": email_subject,
                "TextBody": email_body,
                "MessageStream": "outbound"
            }

            if email:
                payload["ReplyTo"] = email

            response = httpx.post(
                self.api_url,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "X-Postmark-Server-Token": self.api_key
                },
                json=payload,
                timeout=10.0
            )

            if response.status_code == 200:
                logger.info(f"Feedback email sent successfully via Postmark")
                return True
            else:
                logger.error(f"Postmark error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send feedback email: {e}")
            return False


# Singleton instance
email_service = EmailService()
