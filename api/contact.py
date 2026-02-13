"""
Contact and Feedback form handlers for CollectorStream website
"""

from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter()


class ContactForm(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str


class FeedbackForm(BaseModel):
    feedback_type: str
    feedback: str
    email: Optional[EmailStr] = None


@router.post("/contact")
async def submit_contact_form(
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...)
):
    """Handle contact form submissions from website"""
    try:
        success = email_service.send_contact_email(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to send email")

        return {
            "success": True,
            "message": "Thank you! Your message has been sent."
        }

    except Exception as e:
        logger.error(f"Contact form error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit form")


@router.post("/feedback")
async def submit_feedback_form(
    feedback_type: str = Form(...),
    feedback: str = Form(...),
    email: Optional[str] = Form(None)
):
    """Handle feedback form submissions from website"""
    try:
        success = email_service.send_feedback_email(
            feedback_type=feedback_type,
            feedback=feedback,
            email=email
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to send email")

        return {
            "success": True,
            "message": "Thank you! Your feedback has been received."
        }

    except Exception as e:
        logger.error(f"Feedback form error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit form")
