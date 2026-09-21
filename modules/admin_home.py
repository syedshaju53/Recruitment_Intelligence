

import os
import shutil
from datetime import datetime

import pandas as pd
import streamlit as st
from sqlalchemy import text

from backend.database import engine
from backend.database import SessionLocal
from backend.models.admin import Admin
from backend.models.company_contact import CompanyContact
import bcrypt


# ============================================================
# PAGE CONFIGURATION
# ============================================================

def configure_admin_page():

        st.markdown(
            """
            <style>

            .admin-title {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .admin-subtitle {
        color: #9aa1b2;
        font-size: 15px;
        margin-bottom: 25px;
    }

    /* Streamlit metric cards */
    [data-testid="stMetric"] {
        background: #17191f;
        border: 1px solid #2c3038;
        border-radius: 14px;
        padding: 18px 20px;
        min-height: 105px;
        transition: all 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        border-color: #4b5563;
        transform: translateY(-2px);
    }

    [data-testid="stMetricLabel"] {
        font-size: 14px;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        font-size: 30px;
        font-weight: 700;
    }

    .section-title {
        font-size: 22px;
        font-weight: 650;
        margin-top: 28px;
        margin-bottom: 15px;
    }

    .status-open {
        color: #4ade80;
        font-weight: 600;
    }

    .status-closed {
        color: #f87171;
        font-weight: 600;
    }

        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DATABASE HELPERS
# ============================================================

def execute_scalar(query, params=None):

    try:

        with engine.connect() as connection:

            result = connection.execute(
                text(query),
                params or {}
            )

            value = result.scalar()

            return value if value is not None else 0

    except Exception as e:

        st.error(f"Database error: {e}")

        return 0


def execute_dataframe(query, params=None):

    try:

        with engine.connect() as connection:

            result = connection.execute(
                text(query),
                params or {}
            )

            rows = result.fetchall()

            columns = result.keys()

            return pd.DataFrame(
                rows,
                columns=columns
            )

    except Exception as e:

        st.error(f"Database error: {e}")

        return pd.DataFrame()


def execute_query(query, params=None):

    try:

        with engine.begin() as connection:

            connection.execute(
                text(query),
                params or {}
            )

        return True

    except Exception as e:

        st.error(f"Database error: {e}")

        return False


# ============================================================
# ADMIN SESSION
# ============================================================

def admin_logout():

    st.session_state["admin_logged_in"] = False

    if "admin_username" in st.session_state:
        del st.session_state["admin_username"]

    st.rerun()


# ============================================================
# ADMIN LOGIN
# ============================================================

def admin_login():

    st.markdown(
        """
        <div style="text-align:center;">

        <div class="admin-title">
            ⚙️ Admin Portal
        </div>

        <div class="admin-subtitle">
            Recruitment Intelligence Administration
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    left, center, right = st.columns(
        [1, 1.3, 1]
    )

    with center:

        st.markdown("### 🔐 Administrator Login")

        username = st.text_input(
            "Username",
            placeholder="Enter admin username",
            key="admin_username_input"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter admin password",
            key="admin_password_input"
        )

        if st.button(
            "🔐 Sign In",
            type="primary",
            width="stretch",
            key="admin_login_button"
        ):

            db = SessionLocal()

            try:

                admin = (
                    db.query(Admin)
                    .filter(
                        Admin.username == username.strip()
                    )
                    .first()
                )

                if (
                    admin
                    and admin.is_active
                    and bcrypt.checkpw(
                        password.encode("utf-8"),
                        admin.password_hash.encode("utf-8")
                    )
                ):

                    st.session_state[
                        "admin_logged_in"
                    ] = True

                    st.session_state[
                        "admin_username"
                    ] = admin.username

                    st.session_state[
                        "admin_id"
                    ] = admin.admin_id

                    st.success(
                        "✅ Admin login successful."
                    )

                    st.rerun()

                else:

                    st.error(
                        "❌ Invalid administrator credentials."
                    )

            except Exception as e:

                st.error(
                    f"❌ Admin authentication error: {e}"
                )

            finally:

                db.close()

# ============================================================
# METRIC CARD
# ============================================================
def metric_card(title, value, icon):
        st.metric(
            label=f"{icon} {title}",
            value=value
        )

# ============================================================
# ADMIN DASHBOARD
# ============================================================

def admin_dashboard():

    st.markdown(
        """
        <div class="admin-title">
            📊 Admin Dashboard
        </div>

        <div class="admin-subtitle">
            Monitor students, live job openings and recruitment activity.
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # DATABASE COUNTS
    # --------------------------------------------------------

    total_students = execute_scalar(
        """
        SELECT COUNT(*)
        FROM students
        """
    )

    total_jobs = execute_scalar(
        """
        SELECT COUNT(*)
        FROM jobs
        """
    )

    total_live_jobs = execute_scalar(
        """
        SELECT COUNT(*)
        FROM live_jobs
        """
    )

    open_live_jobs = execute_scalar(
        """
        SELECT COUNT(*)
        FROM live_jobs
        WHERE status = 'open'
        """
    )

    saved_jobs = execute_scalar(
        """
        SELECT COUNT(*)
        FROM saved_jobs
        """
    )

    applications = execute_scalar(
        """
        SELECT COUNT(*)
        FROM applications
        """
    )



    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">📈 Recruitment Overview</div>',
        unsafe_allow_html=True
    )

    row1 = st.columns(3)

    with row1[0]:
        metric_card(
            "Total Students",
            total_students,
            "👥"
        )

    with row1[1]:
        metric_card(
            "Total Jobs",
            total_jobs,
            "💼"
        )

    with row1[2]:
        metric_card(
            "Live Job Openings",
            total_live_jobs,
            "🌐"
        )

    row2 = st.columns(3)

    with row2[0]:
        metric_card(
            "Open Jobs",
            open_live_jobs,
            "🟢"
        )

    with row2[1]:
        metric_card(
            "Saved Jobs",
            saved_jobs,
            "🔖"
        )

    with row2[2]:
        metric_card(
            "Applications",
            applications,
            "📋"
        )

    st.write("")

    # --------------------------------------------------------
    # LIVE JOB STATUS
    # --------------------------------------------------------



    st.markdown(
        '<div class="section-title">💼 Live Job Status</div>',
        unsafe_allow_html=True
    )

    job_status = execute_dataframe(
        """
        SELECT
            status,
            COUNT(*) AS count
        FROM live_jobs
        GROUP BY status
        ORDER BY count DESC
        """
    )

    if not job_status.empty:

        total_status_jobs = int(
            job_status["count"].sum()
        )

        st.caption(
            f"{total_status_jobs:,} live job records by current status"
        )

        chart_col, summary_col = st.columns(
            [2.2, 1]
        )

        with chart_col:

            st.bar_chart(
                job_status.set_index("status"),
                width="stretch",
                height=320
            )

        with summary_col:

            st.markdown(
                "#### Status Summary"
            )

            for _, row in job_status.iterrows():

                status = str(
                    row["status"]
                ).title()

                count = int(
                    row["count"]
                )

                st.metric(
                    label=status,
                    value=f"{count:,}"
                )

    else:

        st.info("No live job status data available.")

    # --------------------------------------------------------
    # RECENT LIVE JOBS
    # --------------------------------------------------------



    st.markdown(
        '<div class="section-title">🕐 Recent Live Openings</div>',
        unsafe_allow_html=True
    )

    recent_jobs = execute_dataframe(
        """
        SELECT
            id,
            company_name,
            job_title,
            location,
            work_mode,
            source,
            status,
            posted_date
        FROM live_jobs
        ORDER BY posted_date DESC NULLS LAST
        LIMIT 10
        """
    )

    if not recent_jobs.empty:

        display_jobs = recent_jobs.copy()

        display_jobs.columns = [
            "ID",
            "Company",
            "Job Title",
            "Location",
            "Work Mode",
            "Source",
            "Status",
            "Posted Date"
        ]

        st.caption(
            f"Showing the {len(display_jobs)} most recently posted live openings."
        )

        st.dataframe(
            display_jobs,
            width="stretch",
            hide_index=True,
            height=420,
            column_config={
                "ID": st.column_config.TextColumn(
                    "ID",
                    width="small"
                ),
                "Company": st.column_config.TextColumn(
                    "Company",
                    width="medium"
                ),
                "Job Title": st.column_config.TextColumn(
                    "Job Title",
                    width="large"
                ),
                "Location": st.column_config.TextColumn(
                    "Location",
                    width="medium"
                ),
                "Work Mode": st.column_config.TextColumn(
                    "Work Mode",
                    width="small"
                ),
                "Source": st.column_config.TextColumn(
                    "Source",
                    width="small"
                ),
                "Status": st.column_config.TextColumn(
                    "Status",
                    width="small"
                ),
                "Posted Date": st.column_config.DatetimeColumn(
                    "Posted Date",
                    format="DD MMM YYYY",
                    width="small"
                )
            }
        )

    else:

        st.info("No live jobs found.")

    # --------------------------------------------------------
    # REFRESH
    # --------------------------------------------------------

    if st.button(
        "🔄 Refresh Dashboard",
        width="stretch",
        key="admin_dashboard_refresh"
    ):

        st.rerun()


# ============================================================
# STUDENT MANAGEMENT
# ============================================================

def student_management():

    st.markdown(
        """
        <div class="admin-title">
            👥 Student Management
        </div>

        <div class="admin-subtitle">
            View and manage registered student profiles.
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # STUDENT COUNT
    # --------------------------------------------------------

    total_students = execute_scalar(
        """
        SELECT COUNT(*)
        FROM students
        """
    )

    st.markdown(
        '<div class="section-title">📊 Student Overview</div>',
        unsafe_allow_html=True
    )

    st.metric(
        "Total Registered Students",
        f"{total_students:,}"
    )

    st.write("")

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    search = st.text_input(
        "🔍 Search student",
        placeholder=(
            "Search by student ID, name or email"
        ),
        key="admin_student_search"
    )

    # --------------------------------------------------------
    # STUDENT QUERY
    # --------------------------------------------------------

    if search.strip():

        search_value = (
            f"%{search.strip()}%"
        )

        students = execute_dataframe(
            """
            SELECT
                s.student_id,
                s.student_name,
                s.email,
                s.department,
                p.college,
                p.location,
                p.graduation_year,
                p.cgpa
            FROM students s
            LEFT JOIN student_profiles p
                ON s.student_id = p.student_id
            WHERE
                s.student_id ILIKE :search
                OR s.student_name ILIKE :search
                OR s.email ILIKE :search
            ORDER BY s.student_name
            """,
            {
                "search": search_value
            }
        )

    else:

        students = execute_dataframe(
            """
            SELECT
                s.student_id,
                s.student_name,
                s.email,
                s.department,
                p.college,
                p.location,
                p.graduation_year,
                p.cgpa
            FROM students s
            LEFT JOIN student_profiles p
                ON s.student_id = p.student_id
            ORDER BY s.student_name
            LIMIT 200
            """
        )

    # --------------------------------------------------------
    # DISPLAY STUDENTS
    # --------------------------------------------------------

    if students.empty:

        st.info(
            "No students found."
        )

    else:

        display_students = students.copy()

        display_students.columns = [
            "Student ID",
            "Name",
            "Email",
            "Department",
            "College",
            "Location",
            "Graduation Year",
            "CGPA"
        ]

        st.dataframe(
            display_students,
            width="stretch",
            height=360,
            hide_index=True,
            column_config={
                "Student ID": st.column_config.TextColumn(
                    "Student ID",
                    width="medium"
                ),
                "Name": st.column_config.TextColumn(
                    "Name",
                    width="medium"
                ),
                "Email": st.column_config.TextColumn(
                    "Email",
                    width="large"
                ),
                "Department": st.column_config.TextColumn(
                    "Department",
                    width="medium"
                ),
                "College": st.column_config.TextColumn(
                    "College",
                    width="large"
                ),
                "Location": st.column_config.TextColumn(
                    "Location",
                    width="medium"
                ),
                "Graduation Year": st.column_config.NumberColumn(
                    "Graduation Year",
                    format="%d",
                    width="small"
                ),
                "CGPA": st.column_config.NumberColumn(
                    "CGPA",
                    format="%.2f",
                    width="small"
                )
            }
        )

        st.caption(
            f"Showing {len(display_students)} student record(s)."
        )

    # --------------------------------------------------------
    # STUDENT DETAILS
    # --------------------------------------------------------

    if not students.empty:

        st.markdown(
            '<div class="section-title">👤 Student Details</div>',
            unsafe_allow_html=True
        )

        student_options = {
        f"{row.student_id} — {row.student_name}": row.student_id
        for row in students.itertuples()
    }

        selected_label = st.selectbox(
            "Select Student",
            list(student_options.keys()),
            key="admin_selected_student",
            help="Choose a student to view their complete account information."
        )

        selected_student = student_options[selected_label]
        student = execute_dataframe(
            """
            SELECT *
            FROM students
            WHERE student_id = :student_id
            LIMIT 1
            """,
            {
                "student_id": selected_student
            }
        )

        if not student.empty:

            # Convert database values to display-safe strings
            student_display = student.T.copy()
            student_display.columns = ["Value"]
            student_display["Value"] = student_display["Value"].map(
                lambda value: value.isoformat(sep=" ", timespec="seconds")
                if hasattr(value, "isoformat")
                else str(value)
            )

            st.dataframe(
            student_display,
            width="stretch",
            height=360,
            hide_index=False,
            column_config={
                "Value": st.column_config.TextColumn(
                    "Student Information",
                    width="large"
                )
            }
        )
            #------------------------------------------------
            # REMOVE STUDENT ACCOUNT
            # ------------------------------------------------

            st.divider()

            st.markdown(
                '<div class="section-title">⚠️ Danger Zone</div>',
                unsafe_allow_html=True
            )

            st.warning(
                "Removing this student account permanently deletes the "
                "student profile and associated platform data, including "
                "applications, saved jobs, notifications, and resumes."
            )

            st.caption(
                "This action cannot be undone."
            )

            confirm_delete = st.checkbox(
                "I understand that this action cannot be undone.",
                key=f"confirm_delete_{selected_student}"
            )

            if st.button(
                "🗑️ Remove Student Account",
                type="secondary",
                disabled=not confirm_delete,
                key=f"delete_student_{selected_student}"
            ):

                try:

                    resume_paths = []

                    with engine.begin() as conn:

                        # ------------------------------------------------
                        # Capture physical resume paths before DB deletion
                        # ------------------------------------------------

                        resume_result = conn.execute(
                            text("""
                                SELECT file_path
                                FROM resumes
                                WHERE student_id = :student_id
                            """),
                            {"student_id": selected_student}
                        )

                        resume_paths = [
                            row[0]
                            for row in resume_result
                            if row[0]
                        ]

                        # ------------------------------------------------
                        # Delete dependent records first
                        # ------------------------------------------------

                        conn.execute(
                            text("""
                                DELETE FROM applications
                                WHERE student_id = :student_id
                            """),
                            {"student_id": selected_student}
                        )

                        conn.execute(
                            text("""
                                DELETE FROM notifications
                                WHERE student_id = :student_id
                            """),
                            {"student_id": selected_student}
                        )

                        conn.execute(
                            text("""
                                DELETE FROM resumes
                                WHERE student_id = :student_id
                            """),
                            {"student_id": selected_student}
                        )

                        conn.execute(
                            text("""
                                DELETE FROM saved_jobs
                                WHERE student_id = :student_id
                            """),
                            {"student_id": selected_student}
                        )

                        conn.execute(
                            text("""
                                DELETE FROM student_profiles
                                WHERE student_id = :student_id
                            """),
                            {"student_id": selected_student}
                        )

                        # ------------------------------------------------
                        # Delete main student account
                        # ------------------------------------------------

                        result = conn.execute(
                            text("""
                                DELETE FROM students
                                WHERE student_id = :student_id
                            """),
                            {"student_id": selected_student}
                        )

                    # ----------------------------------------------------
                    # Remove physical resume files
                    # ----------------------------------------------------

                    deleted_files = 0

                    for resume_path in resume_paths:

                        try:

                            path = os.path.abspath(
                                str(resume_path)
                            )

                            if os.path.isfile(path):

                                os.remove(path)

                                deleted_files += 1

                        except Exception as file_error:

                            st.warning(
                                f"Could not remove a resume file: "
                                f"{file_error}"
                            )

                    # ----------------------------------------------------
                    # Remove empty student resume directory
                    # ----------------------------------------------------

                    student_resume_directory = os.path.abspath(
                        os.path.join(
                            "uploads",
                            "resumes",
                            selected_student
                        )
                    )

                    if os.path.isdir(
                        student_resume_directory
                    ):

                        try:

                            shutil.rmtree(
                                student_resume_directory
                            )

                        except Exception:
                            pass

                    # ----------------------------------------------------
                    # Final result
                    # ----------------------------------------------------

                    if result.rowcount == 1:

                        st.success(
                            f"Student account {selected_student} "
                            "has been permanently removed."
                        )

                        if deleted_files > 0:

                            st.info(
                                f"{deleted_files} physical resume file(s) "
                                "were also removed."
                            )

                        st.session_state.pop(
                            "admin_selected_student",
                            None
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Student account could not be found."
                        )

                except Exception as e:

                    st.error(
                        f"Failed to remove student account: {e}"
                    )


# ============================================================
# JOB MANAGEMENT
# ============================================================

def job_management():

    st.markdown(
        """
        <div class="admin-title">
            💼 Job Management
        </div>

        <div class="admin-subtitle">
            Monitor and manage live job openings.
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # JOB COUNTS
    # --------------------------------------------------------

    total_jobs = execute_scalar(
        """
        SELECT COUNT(*)
        FROM live_jobs
        """
    )

    open_jobs = execute_scalar(
        """
        SELECT COUNT(*)
        FROM live_jobs
        WHERE status = 'open'
        """
    )

    closed_jobs = execute_scalar(
        """
        SELECT COUNT(*)
        FROM live_jobs
        WHERE status != 'open'
        """
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Total Live Jobs",
            total_jobs
        )

    with c2:

        st.metric(
            "Open Jobs",
            open_jobs
        )

    with c3:

        st.metric(
            "Closed Jobs",
            closed_jobs
        )

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">🔎 Job Filters</div>',
        unsafe_allow_html=True
    )

    f1, f2, f3 = st.columns(3)

    with f1:

        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "open",
                "closed"
            ],
            key="admin_job_status"
        )

    with f2:

        search_company = st.text_input(
            "Company",
            placeholder="Search company",
            key="admin_job_company"
        )

    with f3:

        search_role = st.text_input(
            "Role",
            placeholder="Search job role",
            key="admin_job_role"
        )

    # --------------------------------------------------------
    # BUILD QUERY
    # --------------------------------------------------------

    query = """
        SELECT
            id,
            job_id,
            company_name,
            job_title,
            department,
            skills,
            experience,
            salary,
            location,
            work_mode,
            posted_date,
            application_url,
            source,
            source_job_id,
            status,
            last_checked
        FROM live_jobs
        WHERE 1 = 1
    """

    params = {}

    if status_filter != "All":

        query += """
            AND status = :status
        """

        params["status"] = status_filter

    if search_company.strip():

        query += """
            AND company_name ILIKE :company
        """

        params["company"] = (
            f"%{search_company.strip()}%"
        )

    if search_role.strip():

        query += """
            AND job_title ILIKE :role
        """

        params["role"] = (
            f"%{search_role.strip()}%"
        )

    query += """
        ORDER BY posted_date DESC NULLS LAST
        LIMIT 300
    """

    jobs = execute_dataframe(
        query,
        params
    )

    # --------------------------------------------------------
    # DISPLAY JOBS
    # --------------------------------------------------------

    if jobs.empty:

        st.info(
            "No jobs match the selected filters."
        )

    else:

        display_jobs = jobs.copy()

        display_jobs.columns = [
            "ID",
            "Job ID",
            "Company",
            "Job Title",
            "Department",
            "Skills",
            "Experience",
            "Salary",
            "Location",
            "Work Mode",
            "Posted Date",
            "Application URL",
            "Source",
            "Source Job ID",
            "Status",
            "Last Checked"
        ]

        st.dataframe(
            display_jobs,
            width="stretch",
            height=420,
            hide_index=True
        )

        st.caption(
            f"Showing {len(display_jobs)} job(s)."
        )

    # --------------------------------------------------------
    # JOB DETAILS
    # --------------------------------------------------------

    if not jobs.empty:

        st.markdown(
            '<div class="section-title">📄 Job Details</div>',
            unsafe_allow_html=True
        )

        job_options = {
        f"{row.company_name} — {row.job_title} ({row.id})": row.id
        for row in jobs.itertuples()
        }

        selected_job_label = st.selectbox(
            "Select Live Job",
            list(job_options.keys()),
            key="admin_selected_live_job"
        )

        selected_job = job_options[selected_job_label]

        selected_data = jobs[
            jobs["id"] == selected_job
        ]

        if not selected_data.empty:

            row = selected_data.iloc[0]

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🏢 Job Information")

                st.write(
                    f"**Company:** {row.get('company_name', '')}"
                )

                st.write(
                    f"**Role:** {row.get('job_title', '')}"
                )

                st.write(
                    f"**Department:** {row.get('department', '')}"
                )

                st.write(
                    f"**Experience:** {row.get('experience', '')}"
                )

                st.write(
                    f"**Skills:** {row.get('skills', '')}"
                )

            with col2:
                st.markdown("#### 📍 Job Location & Status")

                st.write(
                    f"**Location:** {row.get('location', '')}"
                )

                st.write(
                    f"**Work Mode:** {row.get('work_mode', '')}"
                )

                st.write(
                    f"**Salary:** {row.get('salary', '')}"
                )

                st.write(
                    f"**Source:** {row.get('source', '')}"
                )

                status = str(row.get("status", "")).lower()

                if status == "open":
                    st.success("🟢 Status: Open")
                else:
                    st.error("🔴 Status: Closed")

            application_url = row.get("application_url", "")

            if application_url:
                st.markdown("#### 🔗 Application")

                st.link_button(
                    "Open Application Page",
                    str(application_url),
                    width="stretch"
                )
                
    st.divider()

    company_contact_management()
                
                
# ============================================================
# COMPANY RECRUITMENT CONTACT MANAGEMENT
# ============================================================

def company_contact_management():

    st.markdown(
        '<div class="section-title">📧 Company Recruitment Contacts</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Configure the recruitment email used to deliver student applications."
    )

    # --------------------------------------------------------
    # EXISTING COMPANY CONTACTS
    # --------------------------------------------------------

    contacts = execute_dataframe(
        """
        SELECT
            id,
            company_name,
            recruitment_email,
            contact_name,
            is_active,
            created_at,
            updated_at
        FROM company_contacts
        ORDER BY company_name
        """
    )

    if contacts.empty:
        st.info(
            "No company recruitment contacts have been configured yet."
        )
    else:

        display_contacts = contacts.copy()

        display_contacts.columns = [
            "ID",
            "Company",
            "Recruitment Email",
            "Contact Name",
            "Active",
            "Created At",
            "Updated At"
        ]

        st.dataframe(
            display_contacts,
            width="stretch",
            hide_index=True
        )

    # --------------------------------------------------------
    # ADD / UPDATE CONTACT
    # --------------------------------------------------------

    st.markdown("### ➕ Add or Update Company Contact")

    c1, c2 = st.columns(2)

    with c1:

        company_name = st.text_input(
            "Company Name",
            placeholder="Example: Jobgether",
            key="admin_contact_company"
        )

    with c2:

        recruitment_email = st.text_input(
            "Recruitment Email",
            placeholder="Example: careers@company.com",
            key="admin_contact_email"
        )

    c3, c4 = st.columns(2)

    with c3:

        contact_name = st.text_input(
            "Recruiter / Contact Name",
            placeholder="Optional",
            key="admin_contact_name"
        )

    with c4:

        is_active = st.checkbox(
            "Active",
            value=True,
            key="admin_contact_active"
        )

    if st.button(
        "💾 Save Company Contact",
        width="stretch",
        key="save_company_contact"
    ):

        company_name_clean = company_name.strip()
        email_clean = recruitment_email.strip()
        contact_name_clean = contact_name.strip() or None

        if not company_name_clean:
            st.error("Please enter a company name.")

        elif not email_clean:
            st.error("Please enter a recruitment email.")

        elif "@" not in email_clean:
            st.error("Please enter a valid email address.")

        else:

            db = SessionLocal()

            try:

                existing = (
                    db.query(CompanyContact)
                    .filter(
                        CompanyContact.company_name.ilike(
                            company_name_clean
                        )
                    )
                    .first()
                )

                if existing:

                    existing.company_name = company_name_clean
                    existing.recruitment_email = email_clean
                    existing.contact_name = contact_name_clean
                    existing.is_active = is_active

                    db.commit()

                    st.success(
                        f"Updated recruitment contact for {company_name_clean}."
                    )

                else:

                    new_contact = CompanyContact(
                        company_name=company_name_clean,
                        recruitment_email=email_clean,
                        contact_name=contact_name_clean,
                        is_active=is_active
                    )

                    db.add(new_contact)
                    db.commit()

                    st.success(
                        f"Added recruitment contact for {company_name_clean}."
                    )

            except Exception as e:

                db.rollback()

                st.error(
                    f"Unable to save company contact: {e}"
                )

            finally:

                db.close()

            st.rerun()

    # --------------------------------------------------------
    # ACTIVATE / DEACTIVATE
    # --------------------------------------------------------

    if not contacts.empty:

        st.markdown("### 🔄 Manage Contact Status")

        contact_options = {
            f"{row.company_name} — {row.recruitment_email}": row.id
            for row in contacts.itertuples()
        }

        selected_contact_label = st.selectbox(
            "Select Company Contact",
            list(contact_options.keys()),
            key="admin_selected_company_contact"
        )

        selected_contact_id = contact_options[
            selected_contact_label
        ]

        selected_contact = contacts[
            contacts["id"] == selected_contact_id
        ]

        if not selected_contact.empty:

            current_active = bool(
                selected_contact.iloc[0]["is_active"]
            )

            new_status = st.toggle(
                "Recruitment email is active",
                value=current_active,
                key=f"contact_active_{selected_contact_id}"
            )

            if new_status != current_active:

                if st.button(
                    "💾 Update Status",
                    key=f"update_contact_status_{selected_contact_id}",
                    width="stretch"
                ):

                    db = SessionLocal()

                    try:

                        contact = (
                            db.query(CompanyContact)
                            .filter(
                                CompanyContact.id == selected_contact_id
                            )
                            .first()
                        )

                        if contact:

                            contact.is_active = new_status

                            db.commit()

                            status_text = (
                                "activated"
                                if new_status
                                else "deactivated"
                            )

                            st.success(
                                f"{contact.company_name} contact {status_text}."
                            )

                    except Exception as e:

                        db.rollback()

                        st.error(
                            f"Unable to update contact status: {e}"
                        )

                    finally:

                        db.close()

                    st.rerun()

# ============================================================
# FUTURE HIRING ANALYTICS
# ============================================================

def future_hiring_analytics():

    st.markdown(
        """
        <div class="admin-title">
            🔮 Future Hiring Analytics
        </div>

        <div class="admin-subtitle">
            Analyze historical job-market activity and current
            live openings to estimate future hiring activity.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "The Future Hiring model uses job-posting activity "
        "and current live openings as market signals. "
        "It is an estimated hiring-activity measure, not a "
        "guaranteed probability of a candidate being hired."
    )

    # --------------------------------------------------------
    # TRY EXISTING FUTURE HIRING MODULE
    # --------------------------------------------------------

    try:

        from modules.future_hiring import (
            future_hiring_page
        )

        future_hiring_page()

    except Exception as e:

        st.warning(
            "Future Hiring analytics module could not be loaded."
        )

        st.caption(
            f"Details: {e}"
        )

        # ----------------------------------------------------
        # FALLBACK ANALYTICS FROM LIVE JOBS
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">📊 Current Hiring Activity</div>',
            unsafe_allow_html=True
        )

        role_data = execute_dataframe(
            """
            SELECT
                job_title,
                COUNT(*) AS openings
            FROM live_jobs
            WHERE status = 'open'
            GROUP BY job_title
            ORDER BY openings DESC
            LIMIT 20
            """
        )

        if not role_data.empty:

            st.bar_chart(
                role_data.set_index(
                    "job_title"
                )
            )

        else:

            st.info(
                "No live hiring activity available."
            )



# ============================================================
# APPLICATION TRACKING
# ============================================================

def application_tracking():

    # ========================================================
    # PAGE HEADER
    # ========================================================

    st.title("📋 Application Tracking")

    st.caption(
        "Monitor student applications, job status and application activity."
    )

    # ========================================================
    # LOAD APPLICATION DATA
    # ========================================================

    query = """
        SELECT
            a.application_id,
            a.student_id,
            s.student_name,
            s.email,
            s.department,
            a.company_name,
            a.job_title,
            a.status,
            a.applied_at,
            a.last_updated,
            a.official_application_url,
            a.cover_letter,
            a.resume_filename,
            a.company_email,
            a.email_delivery_status,
            a.email_sent_at,
            a.email_error
        FROM applications a
        LEFT JOIN students s
            ON a.student_id = s.student_id
        ORDER BY a.applied_at DESC
    """

    try:
        applications_df = execute_dataframe(query)

    except Exception as e:

        st.error(
            f"Unable to load applications: {e}"
        )

        return

    # ========================================================
    # EMPTY STATE
    # ========================================================

    if applications_df.empty:

        st.info(
            "📭 No student applications have been recorded yet."
        )

        return

    # ========================================================
    # NORMALIZE STATUS
    # ========================================================

    applications_df["status"] = (
        applications_df["status"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

    applications_df["student_name"] = (
        applications_df["student_name"]
        .fillna("Unknown Student")
    )

    applications_df["company_name"] = (
        applications_df["company_name"]
        .fillna("Unknown Company")
    )

    applications_df["job_title"] = (
        applications_df["job_title"]
        .fillna("Unknown Job")
    )

    # ========================================================
    # SUMMARY METRICS
    # ========================================================

    total_applications = len(applications_df)

    applied_count = int(
        (applications_df["status"].str.lower() == "applied").sum()
    )

    other_count = total_applications - applied_count

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Applications",
            total_applications
        )

    with col2:
        st.metric(
            "Applied",
            applied_count
        )

    with col3:
        st.metric(
            "Other Status",
            other_count
        )

    st.write("")

    # ========================================================
    # STATUS OVERVIEW
    # ========================================================

    st.markdown(
        "### 📊 Application Status Overview"
    )

    status_data = (
        applications_df["status"]
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Applications")
    )

    if not status_data.empty:

        chart_col, info_col = st.columns(
            [2, 1]
        )

        with chart_col:

            st.bar_chart(
                status_data.set_index("Status"),
                width="stretch"
            )

        with info_col:

            st.markdown(
                """
                <div style="
                    padding: 18px;
                    border-radius: 12px;
                    border: 1px solid rgba(128,128,128,0.20);
                    background: rgba(128,128,128,0.05);
                ">
                    <div style="
                        font-size: 16px;
                        font-weight: 600;
                        margin-bottom: 12px;
                    ">
                        Status Summary
                    </div>
                """,
                unsafe_allow_html=True
            )

            for _, row in status_data.iterrows():

                status = str(row["Status"])
                count = int(row["Applications"])

                st.write(
                    f"**{status}** — {count}"
                )

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )

    st.divider()

    # ========================================================
    # FILTERS
    # ========================================================

    st.markdown(
        "### 🔎 Filter Applications"
    )

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:

        student_search = st.text_input(
            "Student",
            placeholder="Search student name or email...",
            key="admin_application_student_filter"
        )

    with filter_col2:

        company_search = st.text_input(
            "Company",
            placeholder="Search company...",
            key="admin_application_company_filter"
        )

    with filter_col3:

        status_options = [
            "All"
        ] + sorted(
            applications_df["status"]
            .dropna()
            .unique()
            .tolist()
        )

        selected_status = st.selectbox(
            "Status",
            status_options,
            key="admin_application_status_filter"
        )

    filtered_df = applications_df.copy()

    # Student filter
    if student_search.strip():

        search_value = student_search.strip()

        filtered_df = filtered_df[
            filtered_df["student_name"]
            .astype(str)
            .str.contains(
                search_value,
                case=False,
                na=False
            )
            |
            filtered_df["email"]
            .astype(str)
            .str.contains(
                search_value,
                case=False,
                na=False
            )
        ]

    # Company filter
    if company_search.strip():

        filtered_df = filtered_df[
            filtered_df["company_name"]
            .astype(str)
            .str.contains(
                company_search.strip(),
                case=False,
                na=False
            )
        ]

    # Status filter
    if selected_status != "All":

        filtered_df = filtered_df[
            filtered_df["status"]
            == selected_status
        ]

    # ========================================================
    # FILTER RESULT
    # ========================================================

    st.caption(
        f"Showing {len(filtered_df)} of "
        f"{len(applications_df)} applications"
    )

    # ========================================================
    # APPLICATION TABLE
    # ========================================================

    if filtered_df.empty:

        st.warning(
            "No applications match the selected filters."
        )

        return

    display_df = filtered_df[
        [
            "application_id",
            "student_id",
            "student_name",
            "email",
            "department",
            "company_name",
            "job_title",
            "status",
            "applied_at",
            "last_updated",
            "company_email",
            "email_delivery_status",
            "email_sent_at",
            "email_error"
        ]
    ].copy()

    display_df.columns = [
        "Application ID",
        "Student ID",
        "Student",
        "Email",
        "Department",
        "Company",
        "Job Title",
        "Status",
        "Applied At",
        "Last Updated",
        "Company Email",
        "Email Delivery",
        "Email Sent At",
        "Email Error"
    ]

    st.dataframe(
        display_df,
        width="stretch",
        height=430,
        hide_index=True
    )

    # ========================================================
    # APPLICATION DETAILS
    # ========================================================

    st.divider()

    st.markdown(
        "### 🔍 Application Details"
    )

    application_options = filtered_df[
        "application_id"
    ].tolist()

    def format_application_label(app_id):
        match = filtered_df.loc[filtered_df["application_id"] == app_id]
        if match.empty:
            return f"Application #{app_id}"
        student_name = match["student_name"].iloc[0]
        job_title = match["job_title"].iloc[0]
        return f"Application #{app_id} — {student_name} — {job_title}"

    selected_application_id = st.selectbox(
        "Select an application",
        application_options,
        format_func=format_application_label,
        key="admin_selected_application"
    )

    selected = filtered_df[
        filtered_df["application_id"]
        == selected_application_id
    ].iloc[0]

    # ========================================================
    # DETAILS
    # ========================================================

    detail_col1, detail_col2 = st.columns(2)

    with detail_col1:

        st.markdown("#### 👤 Student")

        st.write(
            f"**Name:** {selected['student_name']}"
        )

        st.write(
            f"**Student ID:** {selected['student_id']}"
        )

        st.write(
            f"**Email:** {selected['email']}"
        )

        st.write(
            f"**Department:** {selected['department']}"
        )

    with detail_col2:

            st.markdown("#### 💼 Job")

            st.write(
                f"**Company:** {selected['company_name']}"
            )

            st.write(
                f"**Job Title:** {selected['job_title']}"
            )

            st.write(
                f"**Status:** {selected['status']}"
            )

            st.write(
                f"**Application ID:** "
                f"{selected['application_id']}"
            )

            # ========================================================
            # COMPANY EMAIL DELIVERY
            # ========================================================

            st.markdown("#### 📧 Company Delivery")

            company_email = selected.get(
                "company_email",
                None
            )

            delivery_status = selected.get(
                "email_delivery_status",
                "Unknown"
            )

            email_sent_at = selected.get(
                "email_sent_at",
                None
            )

            email_error = selected.get(
                "email_error",
                None
            )

            st.write(
                f"**Company Email:** "
                f"{company_email if pd.notna(company_email) else 'Not configured'}"
            )

            st.write(
                f"**Delivery Status:** {delivery_status}"
            )

            if pd.notna(email_sent_at):
                st.write(
                    f"**Email Sent At:** {email_sent_at}"
                )

            if pd.notna(email_error) and str(email_error).strip():
                st.error(
                    f"**Email Error:** {email_error}"
                )

    # ========================================================
    # TIMELINE
    # ========================================================

    st.markdown(
        "#### 🕒 Application Timeline"
    )

    timeline_col1, timeline_col2 = st.columns(2)

    with timeline_col1:

        st.metric(
            "Applied",
            str(selected["applied_at"])
        )

    with timeline_col2:

        st.metric(
            "Last Updated",
            str(selected["last_updated"])
        )

    # ========================================================
    # APPLICATION MATERIALS
    # ========================================================

    st.markdown(
        "#### 📄 Application Materials"
    )

    resume_filename = selected["resume_filename"]

    if resume_filename:
        st.write(
            f"**Resume:** {resume_filename}"
        )
    else:
        st.write(
            "**Resume:** Not provided"
        )

    cover_letter = selected["cover_letter"]

    if cover_letter:

        with st.expander(
            "View Cover Letter"
        ):

            st.write(
                cover_letter
            )

    else:

        st.caption(
            "No cover letter provided."
        )

    # ========================================================
    # OFFICIAL APPLICATION
    # ========================================================

    official_url = selected[
        "official_application_url"
    ]

    if official_url:

        st.markdown(
            "#### 🔗 Official Application"
        )

        st.link_button(
            "Open Application",
            official_url,
            width="stretch"
        )
# ============================================================
# NOTIFICATIONS
# ============================================================

def notifications():

    st.markdown(
        """
        <div class="admin-title">
            🔔 Notifications
        </div>

        <div class="admin-subtitle">
            Create and manage notifications for students.
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # CREATE NOTIFICATION
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">➕ Create Notification</div>',
        unsafe_allow_html=True
    )
    st.caption(
    "Send an announcement, job alert, system update, or important message "
    "to all registered students."
)
    form_col1, form_col2 = st.columns([2, 1])

    with form_col1:

        notification_title = st.text_input(
            "Notification Title",
            placeholder="Example: New job opportunities available",
            key="admin_notification_title"
        )

        notification_message = st.text_area(
            "Message",
            placeholder="Enter notification message...",
            height=140,
            key="admin_notification_message"
        )

    with form_col2:

        notification_type = st.selectbox(
            "Notification Type",
            [
                "General",
                "Job Alert",
                "System",
                "Important"
            ],
            key="admin_notification_type"
        )

        audience = st.selectbox(
            "Audience",
            [
                "All Students"
            ],
            key="admin_notification_audience"
        )

    if st.button(
        "📢 Send Notification",
        type="primary",
        width="stretch",
        key="admin_send_notification"
    ):

        if not notification_title.strip():

            st.error(
                "❌ Notification title is required."
            )

        elif not notification_message.strip():

            st.error(
                "❌ Notification message is required."
            )

        else:

            success = execute_query(
                """
                INSERT INTO notifications
                (
                    student_id,
                    title,
                    message,
                    notification_type,
                    created_at
                )
                SELECT
                    student_id,
                    :title,
                    :message,
                    :notification_type,
                    :created_at
                FROM students
                """,
                {
                    "title":
                        notification_title.strip(),

                    "message":
                        notification_message.strip(),

                    "notification_type":
                        notification_type,

                    "created_at":
                        datetime.utcnow()
                }
            )

    # --------------------------------------------------------
    # EXISTING NOTIFICATIONS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">📨 Existing Notifications</div>',
        unsafe_allow_html=True
    )
    
    st.markdown(
    '<div class="section-title">📨 Existing Notifications</div>',
    unsafe_allow_html=True
)

    st.caption(
    "Recent notifications sent through the admin portal."
)

    existing = execute_dataframe(
        """
        SELECT
            notification_id,
            title,
            message,
            notification_type,
            created_at
        FROM notifications
        ORDER BY created_at DESC
        LIMIT 100
        """
    )

    if existing.empty:

        st.info(
            "No notifications found."
        )

    else:

        display_notifications = existing.copy()

        display_notifications.columns = [
            "Notification ID",
            "Title",
            "Message",
            "Type",
            "Created At"
        ]

        st.dataframe(
        display_notifications,
        width="stretch",
        height=420,
        hide_index=True,
        column_config={
            "Notification ID": st.column_config.NumberColumn(
                "ID",
                width="small"
            ),
            "Title": st.column_config.TextColumn(
                "Title",
                width="medium"
            ),
            "Message": st.column_config.TextColumn(
                "Message",
                width="large"
            ),
            "Type": st.column_config.TextColumn(
                "Type",
                width="small"
            ),
            "Created At": st.column_config.DatetimeColumn(
                "Created At",
                format="DD MMM YYYY, HH:mm",
                width="medium"
            )
        }
    )

        st.caption(
            f"Showing {len(display_notifications)} notification(s)."
        )  
                


# ============================================================
# ADMIN SIDEBAR
# ============================================================

def admin_sidebar():

    st.sidebar.markdown(
        """
        <div style="
            font-size:24px;
            font-weight:700;
        ">
            ⚙️ Admin Portal
        </div>

        <div style="
            color:#9aa1b2;
            font-size:13px;
            margin-bottom:20px;
        ">
            Recruitment Intelligence
        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.divider()

    st.sidebar.markdown(
        "### Navigation"
    )

    page = st.sidebar.radio(
        "Admin Navigation",
        [
            "📊 Dashboard",
            "👥 Student Management",
            "💼 Job Management",
            "📋 Applications",
            "🔔 Notifications"
            

        ],
        label_visibility="collapsed",
        key="admin_navigation"
    )

    st.sidebar.divider()

    st.sidebar.markdown(
        f"""
        👤 **Administrator**

        `{st.session_state.get(
            "admin_username",
            "admin"
        )}`
        """
    )

    st.sidebar.write("")

    if st.sidebar.button(
        "🚪 Logout",
        width="stretch",
        key="admin_logout_button"
    ):

        admin_logout()

    return page


# ============================================================
# MAIN ADMIN PORTAL
# ============================================================

def admin_portal():

    configure_admin_page()

    # --------------------------------------------------------
    # LOGIN CHECK
    # --------------------------------------------------------

    if not st.session_state.get(
        "admin_logged_in",
        False
    ):

        admin_login()

        return

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    page = admin_sidebar()

    # --------------------------------------------------------
    # ROUTING
    # --------------------------------------------------------

    if page == "📊 Dashboard":

        admin_dashboard()

    elif page == "👥 Student Management":

        student_management()

    elif page == "💼 Job Management":

        job_management()

    elif page == "🔮 Future Hiring Analytics":

        future_hiring_analytics()
    elif page == "📋 Applications":

        application_tracking()

    elif page == "🔔 Notifications":

        notifications()


# ============================================================
# COMPATIBILITY WRAPPERS
# ============================================================

def show_admin_home():

    admin_portal()


def show_admin_portal():

    admin_portal()


def admin_home():

    admin_portal()


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    admin_portal()