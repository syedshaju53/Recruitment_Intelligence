import os
import random
import hashlib
import smtplib

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


def send_otp_email(
    email: str,
    otp: str,
    purpose: str
):
    smtp_host = os.getenv(
        "SMTP_HOST",
        "smtp.gmail.com"
    )

    smtp_port = int(
        os.getenv(
            "SMTP_PORT",
            "587"
        )
    )

    smtp_username = os.getenv(
        "SMTP_USERNAME"
    )

    smtp_password = os.getenv(
        "SMTP_PASSWORD"
    )

    sender_email = os.getenv(
        "SMTP_FROM_EMAIL",
        smtp_username
    )

    if not smtp_username or not smtp_password:
        raise RuntimeError(
            "SMTP credentials are not configured. "
            "Set SMTP_USERNAME and SMTP_PASSWORD in .env"
        )

    otp_label = (
        "account registration"
        if purpose == "REGISTER"
        else "password reset"
    )

    message = EmailMessage()

    message["Subject"] = (
        f"Recruitment Intelligence - "
        f"{otp_label.title()} OTP"
    )

    message["From"] = sender_email
    message["To"] = email

    message.set_content(
    f"""
Recruitment Intelligence Portal

Your OTP for {otp_label} is:

{otp}

This OTP will expire in {OTP_EXPIRY_MINUTES} minutes.

Do not share this OTP with anyone.

If you did not request this, please ignore this email.
"""
)

    with smtplib.SMTP(
        smtp_host,
        smtp_port
    ) as server:

        server.starttls()

        server.login(
            smtp_username,
            smtp_password
        )

        server.send_message(message)


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