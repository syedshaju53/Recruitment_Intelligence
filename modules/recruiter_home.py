import streamlit as st
import pandas as pd
from datetime import datetime



# =========================================================
# DATA LOADING
# =========================================================

@st.cache_data
def load_companies():
    return pd.read_csv("data/companies.csv")


@st.cache_data
def load_jobs():
    return pd.read_csv("data/jobs.csv")


@st.cache_data
def load_students():
    return pd.read_csv("data/students.csv")


# =========================================================
# SESSION STATE
# =========================================================

def initialize_recruiter_state():

    if "recruiter_logged_in" not in st.session_state:
        st.session_state.recruiter_logged_in = False

    if "recruiter_company" not in st.session_state:
        st.session_state.recruiter_company = ""

    if "recruiter_page" not in st.session_state:
        st.session_state.recruiter_page = "Dashboard"

    if "prototype_jobs" not in st.session_state:
        jobs_df = load_jobs()
        st.session_state.prototype_jobs = jobs_df.to_dict("records")

    if "applications" not in st.session_state:
        st.session_state.applications = []


# =========================================================
# RECRUITER LOGIN
# =========================================================

def recruiter_login():

    st.title("💼 Recruiter Portal")
    st.subheader("Recruiter Login")

    companies = load_companies()

    company_list = companies["company_name"].dropna().unique().tolist()

    selected_company = st.selectbox(
        "Select Company",
        company_list
    )

    recruiter_email = st.text_input(
        "Recruiter Email",
        placeholder="recruiter@company.com"
    )

    if st.button(
        "Login as Recruiter",
        type="primary",
        width="stretch"
    ):

        if recruiter_email.strip() == "":
            st.warning("Please enter recruiter email.")
            return

        st.session_state.recruiter_logged_in = True
        st.session_state.recruiter_company = selected_company
        st.session_state.recruiter_page = "Dashboard"

        st.rerun()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_company_jobs():

    company = st.session_state.recruiter_company

    jobs = st.session_state.prototype_jobs

    company_jobs = [
        job for job in jobs
        if str(job.get("company_name", "")).strip().lower()
        == company.strip().lower()
    ]

    return company_jobs


def get_company_applications():

    company_jobs = get_company_jobs()

    company_job_roles = {
        str(job.get("role", "")).strip().lower()
        for job in company_jobs
    }

    applications = []

    for application in st.session_state.applications:

        role = str(
            application.get("role", "")
        ).strip().lower()

        if role in company_job_roles:
            applications.append(application)

    return applications


# =========================================================
# DASHBOARD
# =========================================================

def dashboard():

    st.title("📊 Recruiter Dashboard")

    company = st.session_state.recruiter_company

    st.markdown(
        f"### Welcome, {company} Recruiter"
    )

    jobs = get_company_jobs()
    applications = get_company_applications()

    total_jobs = len(jobs)
    total_applicants = len(applications)

    shortlisted = sum(
        1
        for app in applications
        if app.get("status") == "Shortlisted"
    )

    selected = sum(
        1
        for app in applications
        if app.get("status") == "Selected"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Jobs Posted",
            total_jobs
        )

    with col2:
        st.metric(
            "Total Applicants",
            total_applicants
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

    st.subheader("📢 Current Job Openings")

    if not jobs:
        st.info("No jobs posted yet.")
        return

    jobs_df = pd.DataFrame(jobs)

    display_columns = [
        col
        for col in [
            "role",
            "department",
            "openings",
            "salary",
            "location",
            "status"
        ]
        if col in jobs_df.columns
    ]

    st.dataframe(
        jobs_df[display_columns],
        width="stretch",
        hide_index=True
    )


# =========================================================
# POST JOB
# =========================================================

def post_job():

    st.title("📢 Post a New Job")

    company = st.session_state.recruiter_company

    st.info(
        f"Posting job for **{company}**"
    )

    with st.form("post_job_form"):

        role = st.text_input(
            "Job Role",
            placeholder="Example: Data Scientist"
        )

        department = st.selectbox(
            "Department",
            [
                "CSE",
                "ECE",
                "EEE",
                "ME",
                "Civil",
                "IT",
                "Data Science",
                "AI & ML",
                "Other"
            ]
        )

        col1, col2 = st.columns(2)

        with col1:
            openings = st.number_input(
                "Number of Openings",
                min_value=1,
                value=10,
                step=1
            )

        with col2:
            salary = st.text_input(
                "Salary",
                placeholder="₹6–10 LPA"
            )

        location = st.text_input(
            "Location",
            placeholder="Bangalore"
        )

        month = st.selectbox(
            "Hiring Month",
            [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December"
            ]
        )

        application_url = st.text_input(
            "Official Application URL",
            placeholder="https://company.com/careers"
        )

        status = st.selectbox(
            "Job Status",
            [
                "Active",
                "Upcoming",
                "Closed"
            ]
        )

        submitted = st.form_submit_button(
            "🚀 Publish Job",
            type="primary",
            width="stretch"
        )

    if submitted:

        if not role.strip():
            st.error("Please enter the job role.")
            return

        if not salary.strip():
            st.error("Please enter salary information.")
            return

        if not location.strip():
            st.error("Please enter job location.")
            return

        new_job = {
            "company_id": "",
            "company_name": company,
            "role": role.strip(),
            "department": department,
            "month": month,
            "openings": int(openings),
            "salary": salary.strip(),
            "location": location.strip(),
            "status": status,
            "application_url": application_url.strip()
        }

        st.session_state.prototype_jobs.append(
            new_job
        )

        st.success(
            f"✅ {role} has been posted successfully!"
        )

        st.session_state.recruiter_page = "My Jobs"


# =========================================================
# MY JOBS
# =========================================================

def my_jobs():

    st.title("💼 My Jobs")

    jobs = get_company_jobs()

    if not jobs:
        st.info(
            "You have not posted any jobs yet."
        )
        return

    for index, job in enumerate(jobs):

        with st.container(border=True):

            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:

                st.subheader(
                    job.get("role", "Unknown Role")
                )

                st.write(
                    f"🏢 {job.get('company_name', '')}"
                )

                st.write(
                    f"🎓 Department: {job.get('department', '')}"
                )

            with col2:

                st.write(
                    f"📍 {job.get('location', '')}"
                )

                st.write(
                    f"💰 {job.get('salary', '')}"
                )

                st.write(
                    f"👥 Openings: {job.get('openings', 0)}"
                )

            with col3:

                status = job.get(
                    "status",
                    "Active"
                )

                if status == "Active":
                    st.success(status)

                elif status == "Closed":
                    st.error(status)

                else:
                    st.warning(status)


# =========================================================
# APPLICANTS
# =========================================================

def applicants():

    st.title("👥 Applicants")

    applications = get_company_applications()

    if not applications:

        st.info(
            "No student applications available yet."
        )

        st.markdown(
            """
            ### Application Workflow

            **Student applies → Recruiter receives application → Recruiter reviews → Status updated**
            """
        )

        return

    st.subheader(
        f"Applications: {len(applications)}"
    )

    for index, application in enumerate(applications):

        with st.container(border=True):

            col1, col2 = st.columns([3, 2])

            with col1:

                st.subheader(
                    application.get(
                        "student_name",
                        "Unknown Student"
                    )
                )

                st.write(
                    f"🎓 Department: "
                    f"{application.get('department', 'N/A')}"
                )

                st.write(
                    f"💼 Role: "
                    f"{application.get('role', 'N/A')}"
                )

                st.write(
                    f"📅 Applied: "
                    f"{application.get('application_date', 'N/A')}"
                )

            with col2:

                current_status = application.get(
                    "status",
                    "Applied"
                )

                status_options = [
                    "Applied",
                    "Under Review",
                    "Shortlisted",
                    "Interview Scheduled",
                    "Selected",
                    "Rejected"
                ]

                try:
                    current_index = status_options.index(
                        current_status
                    )
                except ValueError:
                    current_index = 0

                new_status = st.selectbox(
                    "Application Status",
                    status_options,
                    index=current_index,
                    key=f"status_{index}"
                )

                if st.button(
                    "Update Status",
                    key=f"update_{index}",
                    width="stretch"
                ):

                    application["status"] = new_status

                    st.success(
                        f"Status updated to {new_status}"
                    )

                    st.rerun()


# =========================================================
# MAIN RECRUITER HOME
# =========================================================

def show_recruiter_home():

    initialize_recruiter_state()

    # Login
    if not st.session_state.recruiter_logged_in:
        recruiter_login()
        return

    # Sidebar
    with st.sidebar:

        st.title("💼 Recruiter")

        st.caption(
            st.session_state.recruiter_company
        )

        st.divider()

        page = st.radio(
            "Navigation",
            [
                "Dashboard",
                "Post Job",
                "My Jobs",
                "Applicants"
            ],
            index=[
                "Dashboard",
                "Post Job",
                "My Jobs",
                "Applicants"
            ].index(
                st.session_state.recruiter_page
            )
        )

        st.session_state.recruiter_page = page

        st.divider()

        if st.button(
            "Logout",
            width="stretch"
        ):

            st.session_state.recruiter_logged_in = False
            st.session_state.recruiter_company = ""
            st.session_state.recruiter_page = "Dashboard"

            st.rerun()

    # Page routing

    if page == "Dashboard":
        dashboard()

    elif page == "Post Job":
        post_job()

    elif page == "My Jobs":
        my_jobs()

    elif page == "Applicants":
        applicants()