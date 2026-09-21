from typing import List, Optional
from pydantic import BaseModel


class StudentProfileCreate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None

    headline: Optional[str] = None
    about: Optional[str] = None

    department: Optional[str] = None
    degree: Optional[str] = None
    graduation_year: Optional[int] = None
    college: Optional[str] = None
    cgpa: Optional[float] = None

    skills: List[str] = []
    projects: List = []
    certifications: List = []
    experience: List = []


class StudentProfileResponse(BaseModel):
    profile_id: str
    student_id: str

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None

    headline: Optional[str] = None
    about: Optional[str] = None

    department: Optional[str] = None
    degree: Optional[str] = None
    graduation_year: Optional[int] = None
    college: Optional[str] = None
    cgpa: Optional[float] = None

    skills: List[str] = []
    projects: List = []
    certifications: List = []
    experience: List = []

    class Config:
        from_attributes = True