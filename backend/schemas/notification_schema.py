from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    title: str
    message: str
    notification_type: str = "General"


class NotificationResponse(BaseModel):
    notification_id: int
    student_id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True