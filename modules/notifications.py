import streamlit as st
from datetime import datetime

from sqlalchemy import text

from backend.database import engine



# ============================================================
# INITIALIZE NOTIFICATION STATE
# ============================================================

def initialize_notification_state():
    """
    Notification data is stored in PostgreSQL.
    Session state is only used for UI state if required.
    """
    pass


# ============================================================
# GET LOGGED-IN STUDENT
# ============================================================

def get_logged_in_student():
    return st.session_state.get("logged_in_student")


# ============================================================
# CREATE NOTIFICATION
# ============================================================

def create_notification(
    title,
    message,
    notification_type="General",
    student_id=None
):
    """
    Create a persistent notification in PostgreSQL.
    """

    student = get_logged_in_student()

    if student_id is None and student:
        student_id = student.get("student_id")

    if not student_id:
        return False

    try:
        with engine.begin() as conn:

            conn.execute(
                text(
                    """
                    INSERT INTO notifications
                    (
                        student_id,
                        title,
                        message,
                        notification_type,
                        is_read,
                        created_at
                    )
                    VALUES
                    (
                        :student_id,
                        :title,
                        :message,
                        :notification_type,
                        FALSE,
                        :created_at
                    )
                    """
                ),
                {
                    "student_id": student_id,
                    "title": title,
                    "message": message,
                    "notification_type": notification_type,
                    "created_at": datetime.utcnow()
                }
            )

        return True

    except Exception as e:

        st.error(
            f"Unable to create notification: {e}"
        )

        return False


# ============================================================
# GET STUDENT NOTIFICATIONS
# ============================================================

def get_student_notifications(student_id=None):

    if student_id is None:

        student = get_logged_in_student()

        if student:
            student_id = student.get("student_id")

    if not student_id:
        return []

    try:

        with engine.connect() as conn:

            rows = conn.execute(
                text(
                    """
                    SELECT
                        notification_id,
                        student_id,
                        title,
                        message,
                        notification_type,
                        is_read,
                        created_at
                    FROM notifications
                    WHERE student_id = :student_id
                    ORDER BY created_at DESC, notification_id DESC
                    """
                ),
                {
                    "student_id": student_id
                }
            ).mappings().all()

        notifications = []

        for row in rows:

            notifications.append(
                {
                    "notification_id":
                        row["notification_id"],

                    "student_id":
                        row["student_id"],

                    "title":
                        row["title"],

                    "message":
                        row["message"],

                    "notification_type":
                        row["notification_type"] or "General",

                    "is_read":
                        False if row["is_read"] is None
                        else bool(row["is_read"]),

                    "created_at":
                        row["created_at"].strftime(
                            "%d-%m-%Y %I:%M %p"
                        )
                        if row["created_at"]
                        else ""
                }
            )

        return notifications

    except Exception as e:

        st.error(
            f"Unable to load notifications: {e}"
        )

        return []


# ============================================================
# UNREAD COUNT
# ============================================================

def get_unread_notification_count(student_id=None):

    if student_id is None:

        student = get_logged_in_student()

        if student:
            student_id = student.get("student_id")

    if not student_id:
        return 0

    try:

        with engine.connect() as conn:

            result = conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM notifications
                    WHERE student_id = :student_id
                    AND COALESCE(is_read, FALSE) = FALSE
                    """
                ),
                {
                    "student_id": student_id
                }
            ).scalar()

        return int(result or 0)

    except Exception as e:

        st.error(
            f"Unable to calculate unread notifications: {e}"
        )

        return 0


# ============================================================
# MARK ONE NOTIFICATION AS READ
# ============================================================

def mark_notification_as_read(notification_id):

    student = get_logged_in_student()

    if not student:
        return False

    student_id = student.get("student_id")

    try:

        with engine.begin() as conn:

            result = conn.execute(
                text(
                    """
                    UPDATE notifications
                    SET is_read = TRUE
                    WHERE notification_id = :notification_id
                    AND student_id = :student_id
                    """
                ),
                {
                    "notification_id": notification_id,
                    "student_id": student_id
                }
            )

        return result.rowcount > 0

    except Exception as e:

        st.error(
            f"Unable to mark notification as read: {e}"
        )

        return False


# ============================================================
# MARK ALL AS READ
# ============================================================

def mark_all_notifications_as_read(student_id=None):

    if student_id is None:

        student = get_logged_in_student()

        if student:
            student_id = student.get("student_id")

    if not student_id:
        return False

    try:

        with engine.begin() as conn:

            conn.execute(
                text(
                    """
                    UPDATE notifications
                    SET is_read = TRUE
                    WHERE student_id = :student_id
                    AND COALESCE(is_read, FALSE) = FALSE
                    """
                ),
                {
                    "student_id": student_id
                }
            )

        return True

    except Exception as e:

        st.error(
            f"Unable to mark notifications as read: {e}"
        )

        return False


# ============================================================
# DELETE NOTIFICATION
# ============================================================

def delete_notification(notification_id):

    student = get_logged_in_student()

    if not student:
        return False

    student_id = student.get("student_id")

    try:

        with engine.begin() as conn:

            result = conn.execute(
                text(
                    """
                    DELETE FROM notifications
                    WHERE notification_id = :notification_id
                    AND student_id = :student_id
                    """
                ),
                {
                    "notification_id": notification_id,
                    "student_id": student_id
                }
            )

        return result.rowcount > 0

    except Exception as e:

        st.error(
            f"Unable to delete notification: {e}"
        )

        return False

# ============================================================
# DELETE NOTIFICATION
# ============================================================

def delete_notification(notification_id):

    student = get_logged_in_student()

    if not student:
        return False

    student_id = student["student_id"]

    try:
        from sqlalchemy import text
        from backend.database import engine

        with engine.begin() as conn:
            result = conn.execute(
                text(
                    """
                    DELETE FROM notifications
                    WHERE notification_id = :notification_id
                    AND student_id = :student_id
                    """
                ),
                {
                    "notification_id": notification_id,
                    "student_id": student_id
                }
            )

        return result.rowcount > 0

    except Exception as e:

        st.error(
            f"Unable to delete notification: {e}"
        )

        return False


# ============================================================
# NOTIFICATION ICON
# ============================================================

def get_notification_icon(notification_type):

    icons = {
        "Application": "📄",
        "Status Update": "🔄",
        "Recommendation": "🎯",
        "Job": "💼",
        "Reminder": "⏰",
        "General": "🔔",
    }

    return icons.get(notification_type, "🔔")


# ============================================================
# NOTIFICATION PAGE
# ============================================================

def notifications_page():

    initialize_notification_state()

    student = get_logged_in_student()

    if not student:
        st.warning("Please login to view notifications.")
        return

    student_id = student.get("student_id")

    notifications = get_student_notifications(student_id)

    unread_count = get_unread_notification_count(student_id)

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.title("🔔 Notifications")

    st.caption(
        "Stay updated with your applications, job opportunities "
        "and recruitment activities."
    )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Total Notifications",
            len(notifications)
        )

    with col2:
        st.metric(
            "Unread",
            unread_count
        )

    st.divider()

    # --------------------------------------------------------
    # ACTIONS
    # --------------------------------------------------------

    if notifications:

        col1, col2 = st.columns(2)

        with col1:
            if unread_count > 0:
                if st.button(
                    "✓ Mark All as Read",
                    use_container_width=True
                ):
                    mark_all_notifications_as_read(student_id)
                    st.rerun()

        with col2:
            
                if st.button(
                    "🗑 Clear All Notifications",
                    use_container_width=True
                ):
                    try:
                        from sqlalchemy import text
                        from backend.database import engine

                        with engine.begin() as conn:
                            conn.execute(
                                text(
                                    """
                                    DELETE FROM notifications
                                    WHERE student_id = :student_id
                                    """
                                ),
                                {
                                    "student_id": student_id
                                }
                            )

                        st.success("Notifications cleared.")
                        st.rerun()

                    except Exception as e:
                        st.error(
                            f"Unable to clear notifications: {e}"
                        )

    st.divider()

    # --------------------------------------------------------
    # EMPTY STATE
    # --------------------------------------------------------

    if not notifications:

        st.info(
            "🔔 You don't have any notifications yet."
        )

        return

    # --------------------------------------------------------
    # NOTIFICATION LIST
    # --------------------------------------------------------

    for notification in notifications:

        notification_id = notification.get(
            "notification_id"
        )

        title = notification.get(
            "title",
            "Notification"
        )

        message = notification.get(
            "message",
            ""
        )

        notification_type = notification.get(
            "notification_type",
            "General"
        )

        created_at = notification.get(
            "created_at",
            ""
        )

        is_read = notification.get(
            "is_read",
            False
        )

        icon = get_notification_icon(
            notification_type
        )

        # ----------------------------------------------------
        # UNREAD
        # ----------------------------------------------------

        if not is_read:

            with st.container(border=True):

                st.markdown(
                    f"### {icon} {title} 🔵"
                )

                st.write(message)

                st.caption(
                    f"{notification_type} • {created_at}"
                )

                if st.button(
                    "Mark as Read",
                    key=f"read_{notification_id}"
                ):
                    mark_notification_as_read(
                        notification_id
                    )

                    st.rerun()

        # ----------------------------------------------------
        # READ
        # ----------------------------------------------------

        else:

            with st.container(border=True):

                st.markdown(
                    f"### {icon} {title}"
                )

                st.write(message)

                st.caption(
                    f"{notification_type} • {created_at}"
                )