import os
import smtplib

from email.message import EmailMessage


def send_application_email(
    recipient_email,
    student_name,
    student_email,
    student_id,
    application_id,
    company_name,
    job_title,
    location=None,
    cover_letter=None,
    resume_path=None,
    resume_filename=None,
    official_application_url=None,
):
    """
    Send a student's application to the configured company
    recruitment email with the student's resume attached.
    """

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
            "SMTP credentials are not configured."
        )

    if not recipient_email:
        raise ValueError(
            "Company recruitment email is not configured."
        )

    if not resume_path:
        raise ValueError(
            "Resume file path is missing."
        )

    if not os.path.exists(resume_path):
        raise FileNotFoundError(
            "Resume file was not found."
        )

    message = EmailMessage()

    message["Subject"] = (
        f"Job Application - {job_title} - "
        f"{student_name}"
    )

    message["From"] = sender_email
    message["To"] = recipient_email
    message["Reply-To"] = student_email

    body = f"""
Dear Recruitment Team,

A student has submitted an application through the
Recruitment Intelligence Portal.

APPLICATION DETAILS
-------------------
Application ID: {application_id}

Student Name: {student_name}
Student ID: {student_id}
Student Email: {student_email}

Company: {company_name}
Job Title: {job_title}
Location: {location or "Not specified"}

COVER LETTER
------------
{cover_letter or "No cover letter provided."}

"""

    if official_application_url:
        body += f"""
OFFICIAL APPLICATION URL
------------------------
{official_application_url}

"""

    body += """
The student's resume is attached to this email.

Regards,
Recruitment Intelligence Portal
"""

    message.set_content(body)

    with open(resume_path, "rb") as resume_file:
        resume_data = resume_file.read()

    filename = (
        resume_filename
        or os.path.basename(resume_path)
    )

    extension = os.path.splitext(filename)[1].lower()

    if extension == ".pdf":
        maintype = "application"
        subtype = "pdf"

    elif extension == ".docx":
        maintype = (
            "application"
        )
        subtype = (
            "vnd.openxmlformats-officedocument"
            ".wordprocessingml.document"
        )

    elif extension == ".doc":
        maintype = "application"
        subtype = "msword"

    else:
        maintype = "application"
        subtype = "octet-stream"

    message.add_attachment(
        resume_data,
        maintype=maintype,
        subtype=subtype,
        filename=filename
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
