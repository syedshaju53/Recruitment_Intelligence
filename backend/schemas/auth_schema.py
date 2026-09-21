from pydantic import BaseModel


class StudentLogin(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    student_id: str
    student_name: str
    username: str
    department: str