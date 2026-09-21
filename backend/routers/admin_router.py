from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import bcrypt

from backend.database import get_db
from backend.models.admin import Admin
from backend.models.otp_verification import OTPVerification
from backend.otp_service import create_and_send_otp, verify_otp


router = APIRouter(
    tags=["Admin"]
)


# ==========================================================
# ADMIN FORGOT PASSWORD - REQUEST OTP
# ==========================================================

@router.post("/forgot-password/request-otp")
def request_admin_forgot_password_otp(
    email: str,
    db: Session = Depends(get_db)
):
    email = email.strip().lower()

    admin = (
        db.query(Admin)
        .filter(Admin.email.ilike(email))
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="No admin account found with this email."
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=403,
            detail="Admin account is inactive."
        )

    try:
        create_and_send_otp(
            db=db,
            email=email,
            purpose="ADMIN_FORGOT_PASSWORD"
        )

        return {
            "message": "OTP sent successfully."
        }

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to send OTP: {str(e)}"
        )


# ==========================================================
# ADMIN FORGOT PASSWORD - VERIFY OTP
# ==========================================================

@router.post("/forgot-password/verify-otp")
def verify_admin_forgot_password_otp(
    email: str,
    otp: str,
    db: Session = Depends(get_db)
):
    success, message = verify_otp(
        db=db,
        email=email,
        otp=otp,
        purpose="ADMIN_FORGOT_PASSWORD"
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail=message
        )

    return {
        "message": message,
        "verified": True
    }


# ==========================================================
# ADMIN FORGOT PASSWORD - RESET
# ==========================================================

@router.post("/forgot-password/reset")
def reset_admin_password(
    email: str,
    otp: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    email = email.strip().lower()

    if len(new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 6 characters."
        )

    admin = (
        db.query(Admin)
        .filter(Admin.email.ilike(email))
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="No admin account found with this email."
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=403,
            detail="Admin account is inactive."
        )

    # ------------------------------------------------------
    # Find the most recent verified OTP
    # ------------------------------------------------------

    otp_record = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.email == email,
            OTPVerification.purpose == "ADMIN_FORGOT_PASSWORD",
            OTPVerification.verified == True
        )
        .order_by(
            OTPVerification.created_at.desc()
        )
        .first()
    )

    if not otp_record:
        raise HTTPException(
            status_code=400,
            detail="OTP has not been verified."
        )

    # ------------------------------------------------------
    # Make sure the verified OTP is still recent
    # ------------------------------------------------------

    verification_window = timedelta(minutes=5)

    if datetime.utcnow() > (
        otp_record.created_at + verification_window
    ):
        raise HTTPException(
            status_code=400,
            detail="OTP verification has expired. Please request a new OTP."
        )

    # ------------------------------------------------------
    # Reset password
    # ------------------------------------------------------

    admin.password_hash = bcrypt.hashpw(
        new_password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    db.commit()

    return {
        "message": "Admin password reset successfully."
    }
