from datetime import datetime
import uuid
import bcrypt
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_student
from backend.models.student import Student
from backend.models.student_profile import StudentProfile
from backend.schemas.student_schema import (
    StudentProfileCreate,
    StudentProfileResponse,
)
from backend.models.otp_verification import OTPVerification
from backend.otp_service import (
    create_and_send_otp,
    verify_otp,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)



from backend.auth import (
    get_current_student,
    create_access_token,
)




router = APIRouter(
    tags=["Students"]
)


# ==========================================================
# STUDENT LOGIN
# ==========================================================

@router.post("/login")
def student_login(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):

    username = username.strip()
    password = password.strip()

    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is required."
        )

    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required."
        )

    # ------------------------------------------------------
    # Find student by username OR email
    # ------------------------------------------------------

    student = (
        db.query(Student)
        .filter(
            (Student.username == username)
            | (Student.email.ilike(username))
        )
        .first()
    )

    if not student:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )


# ------------------------------------------------------
# Verify password
# ------------------------------------------------------

    try:

        password_valid = bcrypt.checkpw(
            password.encode("utf-8"),
            student.password_hash.encode("utf-8")
        )

    except Exception:

        password_valid = False


    if not password_valid:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    # ------------------------------------------------------
    # Create JWT
    # ------------------------------------------------------

    access_token = create_access_token(
        {
            "student_id": student.student_id
        }
    )

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "student_id": student.student_id,
        "student_name": student.student_name,
        "username": student.username,
        "email": student.email,
        "department": student.department,
    }

# ==========================================================
# GET CURRENT STUDENT PROFILE
# ==========================================================

@router.get(
    "/profile/me",
    response_model=StudentProfileResponse
)

def get_student_profile(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):

    profile = (
        db.query(StudentProfile)
        .filter(
            StudentProfile.student_id
            == current_student.student_id
        )
        .first()
    )

    # Create profile automatically if it does not exist
    if not profile:

        profile = StudentProfile(

            student_id=current_student.student_id,

            full_name=current_student.student_name,

            email=current_student.email,

            department=current_student.department,

            degree="B.Tech",

            skills=[],

            projects=[],

            certifications=[],

            experience=[]
        )

        db.add(profile)
        db.commit()
        db.refresh(profile)

    return profile


# ==========================================================
# CREATE / UPDATE PROFILE
# ==========================================================

@router.put(
    "/profile/me",
    response_model=StudentProfileResponse
)
def update_student_profile(

    profile_data: StudentProfileCreate,

    current_student: Student = Depends(
        get_current_student
    ),

    db: Session = Depends(get_db)
):

    profile = (
        db.query(StudentProfile)
        .filter(
            StudentProfile.student_id
            == current_student.student_id
        )
        .first()
    )

    # Create if missing
    if not profile:

        profile = StudentProfile(
            student_id=current_student.student_id
        )

        db.add(profile)

    # Update fields

    profile.full_name = profile_data.full_name
    profile.email = profile_data.email
    profile.phone = profile_data.phone
    profile.location = profile_data.location

    profile.headline = profile_data.headline
    profile.about = profile_data.about

    profile.department = profile_data.department
    profile.degree = profile_data.degree
    profile.graduation_year = profile_data.graduation_year

    profile.college = profile_data.college
    profile.cgpa = profile_data.cgpa

    profile.skills = profile_data.skills
    profile.projects = profile_data.projects
    profile.certifications = profile_data.certifications
    profile.experience = profile_data.experience

    profile.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(profile)

    return profile




@router.post("/register/request-otp")
def request_registration_otp(
    email: str,
    db: Session = Depends(get_db)
):
    email = email.strip().lower()

    existing_student = (
        db.query(Student)
        .filter(Student.email.ilike(email))
        .first()
    )

    if existing_student:
        raise HTTPException(
            status_code=400,
            detail="Email already registered."
        )

    try:
        create_and_send_otp(
            db=db,
            email=email,
            purpose="REGISTER"
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
        
@router.post("/register/verify-otp")
def verify_registration_otp(
    email: str,
    otp: str,
    db: Session = Depends(get_db)
):
    success, message = verify_otp(
        db=db,
        email=email,
        otp=otp,
        purpose="REGISTER"
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
    
    
@router.post("/forgot-password/request-otp")
def request_forgot_password_otp(
    email: str,
    db: Session = Depends(get_db)
):
    email = email.strip().lower()

    student = (
        db.query(Student)
        .filter(Student.email.ilike(email))
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="No account found with this email."
        )

    try:
        create_and_send_otp(
            db=db,
            email=email,
            purpose="FORGOT_PASSWORD"
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
        
        
@router.post("/forgot-password/verify-otp")
def verify_forgot_password_otp(
    email: str,
    otp: str,
    db: Session = Depends(get_db)
):
    success, message = verify_otp(
        db=db,
        email=email,
        otp=otp,
        purpose="FORGOT_PASSWORD"
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
# COMPLETE STUDENT REGISTRATION
# ==========================================================

@router.post("/register")
def register_student(
    student_name: str,
    username: str,
    email: str,
    department: str,
    password: str,
    otp: str,
    db: Session = Depends(get_db)
):
    student_name = student_name.strip()
    username = username.strip()
    email = email.strip().lower()
    department = department.strip()

    if not all([
        student_name,
        username,
        email,
        department,
        password,
        otp
    ]):
        raise HTTPException(
            status_code=400,
            detail="All fields are required."
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 6 characters."
        )

    # ------------------------------------------------------
    # Check existing username
    # ------------------------------------------------------

    existing_username = (
        db.query(Student)
        .filter(Student.username.ilike(username))
        .first()
    )

    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Username already exists."
        )

    # ------------------------------------------------------
    # Check existing email
    # ------------------------------------------------------

    existing_email = (
        db.query(Student)
        .filter(Student.email.ilike(email))
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already registered."
        )

    # ------------------------------------------------------
    # Verify registration OTP
    # ------------------------------------------------------

    success, message = verify_otp(
        db=db,
        email=email,
        otp=otp,
        purpose="REGISTER"
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail=message
        )

    # ------------------------------------------------------
    # Hash password
    # ------------------------------------------------------

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    # ------------------------------------------------------
    # Generate student ID
    # ------------------------------------------------------

    student_id = "STU-" + uuid.uuid4().hex[:8].upper()

    # ------------------------------------------------------
    # Create student
    # ------------------------------------------------------

    student = Student(
        student_id=student_id,
        student_name=student_name,
        username=username,
        email=email,
        password_hash=password_hash,
        department=department
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    return {
        "message": "Account created successfully.",
        "student_id": student.student_id,
        "username": student.username,
        "email": student.email
    }


# ==========================================================
# COMPLETE PASSWORD RESET
# ==========================================================

@router.post("/forgot-password/reset")
def reset_student_password(
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

    # ------------------------------------------------------
    # Find student
    # ------------------------------------------------------

    student = (
        db.query(Student)
        .filter(Student.email.ilike(email))
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="No account found with this email."
        )

    # ------------------------------------------------------
    # Verify OTP
    # ------------------------------------------------------

    success, message = verify_otp(
        db=db,
        email=email,
        otp=otp,
        purpose="FORGOT_PASSWORD"
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail=message
        )

    # ------------------------------------------------------
    # Hash new password
    # ------------------------------------------------------

    student.password_hash = bcrypt.hashpw(
        new_password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    db.commit()

    return {
        "message": "Password reset successfully."
    }