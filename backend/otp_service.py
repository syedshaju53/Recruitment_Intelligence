
import random
import hashlib
import smtplib
import os
import requests
from datetime import datetime, timedelta
from email.message import EmailMessage

from sqlalchemy.orm import Session

from backend.models.otp_verification import OTPVerification


OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5


def generate_otp():
    return str(random.randint(100000, 999999))


def hash_otp(otp: str):
    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


def send_otp_email(email, otp, purpose):
    resend_api_key = os.getenv("RESEND_API_KEY")
    sender_email = os.getenv(
        "RESEND_FROM_EMAIL",
        "onboarding@resend.dev"
    )

    if not resend_api_key:
        raise RuntimeError(
            "RESEND_API_KEY is not configured."
        )

    purpose_text = {
        "REGISTER": "Registration Verification",
        "FORGOT_PASSWORD": "Password Reset Verification",
        "ADMIN_FORGOT_PASSWORD": "Admin Password Reset Verification",
    }.get(purpose, "Verification Code")

    subject = f"{purpose_text} - Recruitment Intelligence"

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Recruitment Intelligence</h2>

            <p>Your verification code is:</p>

            <h1 style="letter-spacing: 6px;">{otp}</h1>

            <p>
                This OTP is valid for
                <strong>{OTP_EXPIRY_MINUTES} minutes</strong>.
            </p>

            <p>
                If you did not request this code, you can safely
                ignore this email.
            </p>

            <hr>

            <p style="color: #666;">
                Recruitment Intelligence Portal
            </p>
        </body>
    </html>
    """

    payload = {
        "from": sender_email,
        "to": [email],
        "subject": subject,
        "html": html_content,
    }

    headers = {
        "Authorization": f"Bearer {resend_api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://api.resend.com/emails",
        headers=headers,
        json=payload,
        timeout=15,
    )

    if not response.ok:
        try:
            error_data = response.json()
        except Exception:
            error_data = response.text

        raise RuntimeError(
            f"Resend email API failed "
            f"(HTTP {response.status_code}): {error_data}"
        )

    return response.json()

def create_and_send_otp(
    db: Session,
    email: str,
    purpose: str
):
    email = email.strip().lower()

    otp = generate_otp()
    otp_hash = hash_otp(otp)

    expires_at = (
        datetime.utcnow()
        + timedelta(
            minutes=OTP_EXPIRY_MINUTES
        )
    )

    # Invalidate previous OTPs
    previous_otps = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.email == email,
            OTPVerification.purpose == purpose,
            OTPVerification.verified == False
        )
        .all()
    )

    for old_otp in previous_otps:
        old_otp.verified = True

    otp_record = OTPVerification(
        email=email,
        otp_hash=otp_hash,
        purpose=purpose,
        expires_at=expires_at,
        verified=False,
        attempts=0
    )

    db.add(otp_record)
    db.commit()
    db.refresh(otp_record)

    # IMPORTANT:
    # OTP is sent through email.
    # It is NOT returned to the frontend.
    send_otp_email(
        email=email,
        otp=otp,
        purpose=purpose
    )

    return otp_record


def verify_otp(
    db: Session,
    email: str,
    otp: str,
    purpose: str
):
    email = email.strip().lower()
    otp = otp.strip()

    record = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.email == email,
            OTPVerification.purpose == purpose,
            OTPVerification.verified == False
        )
        .order_by(
            OTPVerification.created_at.desc()
        )
        .first()
    )

    if not record:
        return False, "OTP not found or already used."

    if datetime.utcnow() > record.expires_at:
        return False, "OTP has expired."

    if record.attempts >= MAX_OTP_ATTEMPTS:
        return False, "Maximum OTP attempts exceeded."

    record.attempts += 1

    if record.otp_hash != hash_otp(otp):
        db.commit()

        remaining = (
            MAX_OTP_ATTEMPTS
            - record.attempts
        )

        return (
            False,
            f"Invalid OTP. {remaining} attempts remaining."
        )

    record.verified = True

    db.commit()

    return True, "OTP verified successfully."