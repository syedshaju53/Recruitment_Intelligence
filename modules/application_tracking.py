from datetime import datetime
import streamlit as st
import pandas as pd

from api.client import APIClient


# ============================================================
# SESSION STATE
# ============================================================

def initialize_application_state():

    if "selected_application_job" not in st.session_state:
        st.session_state.selected_application_job = None

    if "show_application_form" not in st.session_state:
        st.session_state.show_application_form = False

    if "application_success" not in st.session_state:
        st.session_state.application_success = None


initialize_application_state()


# ============================================================
# LOGGED-IN STUDENT
# ============================================================

def get_logged_in_student():

    return st.session_state.get(
        "logged_in_student"
    )


# ============================================================
# API CLIENT
# ============================================================

def get_api_client():

    api_client = st.session_state.get(
        "api_client"
    )

    if api_client:
        return api_client

    access_token = st.session_state.get(
        "access_token"
    )

    if not access_token:
        return None

    try:

        api_client = APIClient()

        # Support clients that expose set_token()
        if hasattr(api_client, "set_token"):
            api_client.set_token(access_token)

        st.session_state.api_client = api_client

        return api_client

    except Exception:
        return None


# ============================================================
# LIVE JOB ID
# ============================================================

def get_live_job_id(job):

    if isinstance(job, pd.Series):

        value = job.get("live_job_id")

        if value is None or pd.isna(value):
            value = job.get("id")

    elif isinstance(job, dict):

        value = job.get("live_job_id")

        if value is None or pd.isna(value):
            value = job.get("id")

    else:

        value = ""

    if value is None or pd.isna(value):
        return ""

    value = str(value).strip()

    if not value:
        return ""

    try:
        return str(int(float(value)))
    except (ValueError, TypeError):
        return value


# ============================================================
# JOB TITLE
# ============================================================

def get_job_title(job):

    if isinstance(job, pd.Series):

        value = job.get(
            "job_title",
            job.get(
                "role",
                ""
            )
        )

    else:

        value = job.get(
            "job_title",
            job.get(
                "role",
                ""
            )
        )

    if pd.isna(value):
        return ""

    return str(value).strip()


# ============================================================
# COMPANY NAME
# ============================================================

def get_company_name(job):

    value = job.get(
        "company_name",
        ""
    )

    if pd.isna(value):
        return ""

    return str(value).strip()


# ============================================================
# APPLICATION URL
# ============================================================

def normalize_application_url(url):

    if pd.isna(url):
        return ""

    url = str(url).strip()

    if not url:
        return ""

    if not url.startswith(
        (
            "http://",
            "https://"
        )
    ):
        url = "https://" + url

    return url


# ============================================================
# GET STUDENT APPLICATIONS
# ============================================================

def get_student_applications():

    api_client = get_api_client()

    if not api_client:
        return []

    try:

        response = api_client.get_my_applications()

        if response.status_code != 200:
            return []

        data = response.json()

        if isinstance(data, list):
            return data

        if isinstance(data, dict):

            return data.get(
                "applications",
                []
            )

    except Exception as e:

        st.error(
            f"Unable to load applications: {e}"
        )

    return []


# ============================================================
# CHECK WHETHER STUDENT ALREADY APPLIED
# ============================================================

def has_applied(job):

    live_job_id = get_live_job_id(job)

    if not live_job_id:
        return False

    applications = get_student_applications()

    for application in applications:

        existing_live_job_id = application.get(
            "live_job_id"
        )

        if (
            existing_live_job_id is not None
            and
            str(existing_live_job_id)
            == str(live_job_id)
        ):

            return True

    return False


# ============================================================
# OPEN APPLICATION FORM
# ============================================================

def open_application_form(job):

    if isinstance(job, pd.Series):

        job = job.to_dict()

    st.session_state.selected_application_job = job

    st.session_state.show_application_form = True

    st.rerun()


# ============================================================
# APPLICATION FORM
# ============================================================

def application_form(job):

    student = get_logged_in_student()

    if not student:

        st.error(
            "Please login first."
        )

        return

    live_job_id = get_live_job_id(job)

    if not live_job_id:

        st.error(
            "Live job ID is missing."
        )

        return

    company = get_company_name(job)

    role = get_job_title(job)

    department = str(
        job.get(
            "department",
            "-"
        )
    )

    location = str(
        job.get(
            "location",
            "-"
        )
    )

    salary = str(
        job.get(
            "salary",
            "-"
        )
    )

    work_mode = str(
        job.get(
            "work_mode",
            "-"
        )
    )

    source = str(
        job.get(
            "source",
            "Live Job Source"
        )
    )

    # ========================================================
    # HEADER
    # ========================================================

    st.markdown(
        "## 📝 Job Application"
    )

    st.info(
        "Submit your application through the recruitment portal. "
        "Your application will be recorded in My Applications."
    )

    # ========================================================
    # JOB DETAILS
    # ========================================================

    st.subheader(
        "💼 Job Details"
    )
    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "← Cancel",
            use_container_width=True,
            key=f"cancel_application_{live_job_id}"
        ):
            st.session_state.show_application_form = False
            st.session_state.selected_application_job = None
            st.rerun()

    with col2:

        if st.button(
            "🚀 Submit Application",
            type="primary",
            use_container_width=True,
            key=f"submit_application_{live_job_id}"
        ):

            if not confirmation:
                st.error("Please confirm that the information provided is correct.")
                st.stop()

            if resume is None:
                st.error("Please upload your resume before submitting.")
                st.stop()

            api_client = get_api_client()

            if not api_client:
                st.error("Unable to connect to the application server.")
                st.stop()

            resume_upload_response = api_client.upload_resume(
                file_name=resume.name,
                file_data=resume.getvalue(),
                mime_type=resume.type
            )

            if resume_upload_response.status_code not in (200, 201):
                st.error(f"Resume upload failed: {resume_upload_response.text}")
                st.stop()

            resume_data = resume_upload_response.json()
            resume_id = resume_data.get("resume_id")

            if not resume_id:
                st.error("Resume ID was not returned by the server.")
                st.stop()

            response = api_client.apply_for_job(
                job_id=None,
                live_job_id=int(live_job_id),
                cover_letter=cover_letter,
                resume_filename=resume.name,
                resume_id=resume_id
            )

            if response.status_code == 201:
                application_data = response.json()

                st.session_state.application_success = {
                    "application_id": application_data.get("application_id"),
                    "company": application_data.get("company_name", company),
                    "role": application_data.get("job_title", role),
                    "live_job_id": application_data.get("live_job_id", live_job_id),
                    "source": application_data.get("source", source),
                    "status": application_data.get("status", "Applied")
                }

                st.session_state.show_application_form = False
                st.session_state.selected_application_job = None
                st.rerun()

            else:
                st.error(f"Application failed: {response.text}")


# ============================================================
# SHOW SELECTED APPLICATION FORM
# ============================================================

def show_selected_application_form():

    if not st.session_state.get(
        "show_application_form",
        False
    ):

        return

    job = st.session_state.get(
        "selected_application_job"
    )

    if not job:

        st.session_state.show_application_form = False

        return

    application_form(job)


# ============================================================
# APPLY BUTTON
# ============================================================

def render_apply_button(job):

    live_job_id = get_live_job_id(job)
    
    st.info(
    f"DEBUG → live_job_id={live_job_id}, "
    f"type={type(live_job_id).__name__}"
)
    

    if not live_job_id:

        st.error(
            "Unable to apply: live job ID is missing."
        )

        return

    if has_applied(job):

        st.success(
            "✅ Applied"
        )

        return

    if st.button(
        "🚀 Apply Now",
        type="primary",
        use_container_width=True,
        key=f"apply_live_job_{live_job_id}"
    ):

        open_application_form(job)


# ============================================================
# OFFICIAL WEBSITE BUTTON
# ============================================================

def render_official_button(job):

    url = normalize_application_url(
        job.get(
            "application_url",
            ""
        )
    )

    live_job_id = get_live_job_id(job)

    if url:

        st.link_button(
            "🌐 Official Website",
            url,
            use_container_width=True
        )

    else:

        st.button(
            "🌐 Official Website",
            disabled=True,
            use_container_width=True,
            key=f"official_disabled_{live_job_id}"
        )


# ============================================================
# STATUS BADGE
# ============================================================

def status_message(status):

    status = str(
        status
    ).strip().lower()

    if status == "applied":
        return "🟡 Applied"

    if status == "received":
        return "🔵 Received"

    if status == "under review":
        return "🔵 Under Review"

    if status == "shortlisted":
        return "🟣 Shortlisted"

    if status == "interview":
        return "🟠 Interview"

    if status == "interview scheduled":
        return "🟠 Interview Scheduled"

    if status == "selected":
        return "🟢 Selected"

    if status == "rejected":
        return "🔴 Rejected"

    return str(status)


# ============================================================
# APPLICATION TIMELINE
# ============================================================

def show_application_timeline(application):

    history = application.get(
        "status_history",
        []
    )

    if not history:
        return

    st.markdown(
        "#### 📌 Status History"
    )

    for item in reversed(history):

        status = item.get(
            "status",
            "-"
        )

        date = item.get(
            "date",
            "-"
        )

        source = item.get(
            "source",
            "System"
        )

        st.write(
            f"**{status}** — {date} — {source}"
        )


# ============================================================
# APPLICATION CARD
# ============================================================

def application_card(application):

    company = (
        application.get("company_name")
        or "Company"
    )

    role = (
        application.get("job_title")
        or application.get("role")
        or "Role"
    )

    status = (
        application.get("status")
        or "Applied"
    )

    application_id = (
        application.get("application_id")
        or "-"
    )

    live_job_id = (
        application.get("live_job_id")
        or "-"
    )

    source = (
        application.get("source")
        or "Live Job Source"
    )

    source_job_id = (
        application.get("source_job_id")
        or "-"
    )

    applied_date = (
        application.get("applied_at")
        or application.get("applied_date")
        or "-"
    )

    last_updated = (
        application.get("last_updated")
        or "-"
    )

    resume_filename = (
        application.get("resume_filename")
        or "-"
    )

    with st.container(border=True):

        st.markdown(
            f"### {role}"
        )

        st.write(
            f"🏢 **{company}**"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.write(
                f"🆔 **Application ID:** "
                f"{application_id}"
            )

        with col2:

            st.write(
                f"📅 **Applied:** "
                f"{applied_date}"
            )

        with col3:

            st.write(
                f"📌 **Status:** "
                f"{status_message(status)}"
            )

        st.write(
            f"**Live Job ID:** {live_job_id}"
        )

        st.write(
            f"**Source:** {source}"
        )

        if source_job_id != "-":

            st.write(
                f"**Source Job ID:** {source_job_id}"
            )

        if resume_filename != "-":

            st.write(
                f"📄 **Resume:** {resume_filename}"
            )

        st.write(
            f"**Last Updated:** {last_updated}"
        )

        show_application_timeline(
            application
        )


# ============================================================
# SUCCESS MESSAGE
# ============================================================

def show_application_success():

    success = st.session_state.get(
        "application_success"
    )

    if not success:
        return

    # --------------------------------------------------------
    # Handle old boolean success value
    # --------------------------------------------------------

    if isinstance(success, bool):

        if success is True:

            st.success(
                "🎉 Application submitted successfully!"
            )

            st.info(
                "Your application has been submitted "
                "successfully and recorded in the portal."
            )

        return

    # --------------------------------------------------------
    # Expected success dictionary
    # --------------------------------------------------------

    if not isinstance(success, dict):

        st.session_state["application_success"] = None

        return

    st.success(
        "🎉 Application submitted successfully!"
    )

    st.info(
        f"""
        **Application ID:** {success.get("application_id", "-")}

        **Company:** {success.get("company", "-")}

        **Role:** {success.get("role", "-")}

        **Live Job ID:** {success.get("live_job_id", "-")}

        **Source:** {success.get("source", "-")}

        **Status:** {success.get("status", "Applied")}
        """
    )

    st.caption(
        "Your application has been recorded in the recruitment portal. "
        "Company-side status synchronization requires an authorized "
        "company/ATS integration."
    )


# ============================================================
# APPLICATION TRACKING PAGE
# ============================================================

def application_tracking_page():

    student = get_logged_in_student()

    if not student:

        st.warning(
            "Please login to view your applications."
        )

        return

    st.markdown(
        '<div class="student-title">📋 My Applications</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="student-subtitle">'
        'Track applications submitted through the portal.'
        '</div>',
        unsafe_allow_html=True
    )

    # ========================================================
    # SUCCESS MESSAGE
    # ========================================================

    show_application_success()

    # ========================================================
    # LOAD FROM BACKEND
    # ========================================================

    applications = get_student_applications()

    # Only show applications created from the current live_jobs system.
    # Old legacy applications may have live_job_id = None.
    applications = [
        app
        for app in applications
        if app.get("live_job_id") is not None
]

    # ========================================================
    # METRICS
    # ========================================================

    total = len(applications)

    applied = sum(
        1
        for app in applications
        if str(
            app.get(
                "status",
                ""
            )
        ).lower()
        == "applied"
    )

    shortlisted = sum(
        1
        for app in applications
        if str(
            app.get(
                "status",
                ""
            )
        ).lower()
        == "shortlisted"
    )

    selected = sum(
        1
        for app in applications
        if str(
            app.get(
                "status",
                ""
            )
        ).lower()
        == "selected"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Total Applications",
            total
        )

    with col2:

        st.metric(
            "Applied",
            applied
        )

    with col3:

        st.metric(
            "Shortlisted",
            shortlisted
        )

    with col4:

        st.metric(
            "Selected",
            selected
        )

    st.divider()

    # ========================================================
    # NO APPLICATIONS
    # ========================================================

    if not applications:

        st.info(
            "You have not submitted any applications yet."
        )

        st.markdown(
            """
            ### 🔎 Start Your Job Search

            Go to **Find Jobs** or **Live Recommended Jobs**
            and click **Apply Now**.
            """
        )

        return

    # ========================================================
    # SEARCH / FILTER
    # ========================================================

    col1, col2 = st.columns(2)

    with col1:

        search = st.text_input(
            "🔎 Search Applications",
            placeholder="Company or role...",
            key="application_search"
        )

    with col2:

        statuses = [
            "All",
            "Applied",
            "Received",
            "Under Review",
            "Shortlisted",
            "Interview",
            "Selected",
            "Rejected",
        ]

        selected_status = st.selectbox(
            "Status",
            statuses,
            key="application_status_filter"
        )

    # ========================================================
    # FILTER
    # ========================================================

    filtered = applications

    if search:

        search_text = search.lower()

        filtered = [

            app

            for app in filtered

            if (
                search_text
                in str(
                    app.get(
                        "company_name",
                        ""
                    )
                ).lower()
            )

            or

            (
                search_text
                in str(
                    app.get(
                        "job_title",
                        app.get(
                            "role",
                            ""
                        )
                    )
                ).lower()
            )

        ]

    if selected_status != "All":

        filtered = [

            app

            for app in filtered

            if str(
                app.get(
                    "status",
                    ""
                )
            ).lower()
            ==
            selected_status.lower()

        ]

    # ========================================================
    # DISPLAY
    # ========================================================

    st.markdown(
        f"### Applications ({len(filtered)})"
    )

    for application in filtered:

        application_card(
            application
        )


# ============================================================
# OPTIONAL ADMIN/PROTOTYPE STATUS UPDATE
# ============================================================

def update_application_status(
    application_id,
    new_status,
    source="Company / ATS"
):

    """
    This function is intentionally kept as a prototype helper.

    The real production implementation should update the
    application through an authorized company/ATS integration.
    """

    st.warning(
        "Application status updates should be handled by "
        "an authorized company/ATS integration."
    )

    return False