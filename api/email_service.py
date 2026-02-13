"""
Email service for CollectorStream contact and feedback forms
"""

import boto3
from botocore.exceptions import ClientError
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, region: str = "us-east-2"):
        self.ses_client = boto3.client('ses', region_name=region)
        self.from_email = "noreply@collectorstream.com"
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
            email_body = f"""
New contact form submission from CollectorStream:

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}

---
Reply to: {email}
"""

            response = self.ses_client.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [self.to_email]},
                Message={
                    'Subject': {'Data': email_subject},
                    'Body': {'Text': {'Data': email_body}}
                },
                ReplyToAddresses=[email]
            )

            logger.info(f"Contact email sent successfully: {response['MessageId']}")
            return True

        except ClientError as e:
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
            email_body = f"""
New feedback submission from CollectorStream:

Type: {feedback_type}
User Email: {email or 'Not provided'}

Feedback:
{feedback}

---
"""
            if email:
                email_body += f"Reply to: {email}"

            response = self.ses_client.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [self.to_email]},
                Message={
                    'Subject': {'Data': email_subject},
                    'Body': {'Text': {'Data': email_body}}
                },
                ReplyToAddresses=[email] if email else []
            )

            logger.info(f"Feedback email sent successfully: {response['MessageId']}")
            return True

        except ClientError as e:
            logger.error(f"Failed to send feedback email: {e}")
            return False


# Singleton instance
email_service = EmailService()
