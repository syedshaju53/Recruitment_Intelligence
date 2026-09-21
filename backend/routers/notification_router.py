from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth import get_current_student
from backend.database import get_db
from backend.models.notification import Notification
from backend.models.student import Student
from backend.schemas.notification_schema import (
    NotificationCreate,
    NotificationResponse,
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


# ---------------------------------------------------------
# CREATE NOTIFICATION
# ---------------------------------------------------------

@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_notification(
    notification_data: NotificationCreate,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    notification = Notification(
        student_id=current_student.student_id,
        title=notification_data.title,
        message=notification_data.message,
        notification_type=notification_data.notification_type,
        is_read=False
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


# ---------------------------------------------------------
# GET MY NOTIFICATIONS
# ---------------------------------------------------------

@router.get(
    "",
    response_model=list[NotificationResponse]
)
def get_my_notifications(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    notifications = (
        db.query(Notification)
        .filter(
            Notification.student_id == current_student.student_id
        )
        .order_by(Notification.created_at.desc())
        .all()
    )

    return notifications


# ---------------------------------------------------------
# GET UNREAD COUNT
# ---------------------------------------------------------

@router.get(
    "/unread-count"
)
def get_unread_notification_count(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    count = (
        db.query(Notification)
        .filter(
            Notification.student_id == current_student.student_id,
            Notification.is_read == False
        )
        .count()
    )

    return {
        "unread_count": count
    }


# ---------------------------------------------------------
# MARK ONE NOTIFICATION AS READ
# ---------------------------------------------------------

@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse
)
def mark_notification_as_read(
    notification_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.notification_id == notification_id,
            Notification.student_id == current_student.student_id
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification


# ---------------------------------------------------------
# MARK ALL AS READ
# ---------------------------------------------------------

@router.patch(
    "/read-all"
)
def mark_all_notifications_as_read(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    updated_count = (
        db.query(Notification)
        .filter(
            Notification.student_id == current_student.student_id,
            Notification.is_read == False
        )
        .update(
            {
                Notification.is_read: True
            },
            synchronize_session=False
        )
    )

    db.commit()

    return {
        "message": "All notifications marked as read",
        "updated_count": updated_count
    }