from pathlib import Path
import json
from urllib import response
import requests
import os
import streamlit as st
import pandas as pd

from api.client import APIClient

from modules.recommended_jobs import show_recommended_jobs
from modules.future_hiring import future_hiring_page
from modules.role_intelligence import show_role_intelligence
from modules.application_tracking import (
    application_tracking_page,
)

from modules.notifications import (
    notifications_page,
    initialize_notification_state,
)



API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

STUDENTS_FILE = DATA_DIR / "students.csv"
JOBS_FILE = DATA_DIR / "jobs.csv"


# ============================================================
# OPTIONAL LOCAL DATA LOADERS
# ============================================================

@st.cache_data
def load_students():
    """
    Load local students.csv only for legacy/demo UI support.

    Authentication is handled by FastAPI.
    PostgreSQL remains the source of truth.
    """

    if not STUDENTS_FILE.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(STUDENTS_FILE)

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
            .str.lower()
        )

        return df

    except Exception:
        return pd.DataFrame()


@st.cache_data
def load_jobs():
    """
    Legacy helper.

    Current job data should come from FastAPI/PostgreSQL.
    """

    if not JOBS_FILE.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(JOBS_FILE)

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
            .str.lower()
        )

        return df

    except Exception:
        return pd.DataFrame()


# ============================================================
# SESSION STATE
# ============================================================

def initialize_student_state():

    defaults = {

        "student_logged_in": False,

        "access_token": None,

        "logged_in_student": None,

        "student_page": "Dashboard",

        "student_profile": {},

        "student_profiles_by_id": {},

        "saved_jobs": [],

        "applications": [],

        "student_resume": None,

        "student_documents": [],

        "selected_application_job": None,

        "show_application_form": False,

        "auth_mode": "Sign In",

        "profile_loaded": False,

        "profile_loading": False,

        "application_success": False,

        "company_search": "",

        "role_search": "",

    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value

    # --------------------------------------------------------
    # API CLIENT
    # --------------------------------------------------------

    if "api_client" not in st.session_state:

        st.session_state.api_client = APIClient()

    # --------------------------------------------------------
    # RESTORE TOKEN
    # --------------------------------------------------------

    if st.session_state.get("access_token"):

        st.session_state.api_client.set_token(
            st.session_state.access_token
        )


# ============================================================
# API CLIENT
# ============================================================

def get_api_client():

    api_client = st.session_state.get("api_client")

    if api_client is None:

        api_client = APIClient()

        st.session_state.api_client = api_client

    token = st.session_state.get("access_token")

    if token:
        api_client.set_token(token)

    return api_client


# ============================================================
# LOGGED-IN STUDENT
# ============================================================

def get_logged_in_student():

    return st.session_state.get(
        "logged_in_student"
    )


# ============================================================
# JSON HELPERS
# ============================================================

def safe_json_load(value, default=None):

    if default is None:
        default = []

    if value is None:
        return default

    if isinstance(value, list):
        return value

    if isinstance(value, dict):
        return value

    if not isinstance(value, str):
        return default

    value = value.strip()

    if not value:
        return default

    try:

        parsed = json.loads(value)

        return parsed

    except Exception:

        return default


def json_string(value):

    try:

        return json.dumps(
            value,
            ensure_ascii=False
        )

    except Exception:

        return "[]"


# ============================================================
# NORMALIZE PROFILE FROM API
# ============================================================

def normalize_profile(profile_data):
    """
    Normalize the profile returned by FastAPI.

    PostgreSQL/FastAPI currently stores these fields directly:
        full_name
        email
        phone
        location
        headline
        about
        department
        degree
        graduation_year
        college
        cgpa
        skills
        projects
        certifications
        experience
    """

    if not isinstance(profile_data, dict):
        profile_data = {}

    student = get_logged_in_student() or {}

    # --------------------------------------------------------
    # STUDENT ID
    # --------------------------------------------------------

    student_id = str(
        profile_data.get(
            "student_id",
            student.get("student_id", "")
        )
    )

    # --------------------------------------------------------
    # LIST FIELDS
    # --------------------------------------------------------

    skills = safe_json_load(
        profile_data.get("skills"),
        []
    )

    projects = safe_json_load(
        profile_data.get("projects"),
        []
    )

    certifications = safe_json_load(
        profile_data.get("certifications"),
        []
    )

    experience = safe_json_load(
        profile_data.get("experience"),
        []
    )

    # Make sure they are lists
    if not isinstance(skills, list):
        skills = []

    if not isinstance(projects, list):
        projects = []

    if not isinstance(certifications, list):
        certifications = []

    if not isinstance(experience, list):
        experience = []

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    profile = {

        "student_id": student_id,

        # Use profile data first.
        # Fall back to login data if necessary.
        "full_name": str(
            profile_data.get(
                "full_name",
                student.get("student_name", "")
            ) or ""
        ),

        "email": str(
            profile_data.get(
                "email",
                student.get("email", "")
            ) or ""
        ),

        "phone": str(
            profile_data.get(
                "phone",
                ""
            ) or ""
        ),

        "date_of_birth": str(
            profile_data.get(
                "date_of_birth",
                ""
            ) or ""
        ),

        "gender": str(
            profile_data.get(
                "gender",
                ""
            ) or ""
        ),

        "location": str(
            profile_data.get(
                "location",
                ""
            ) or ""
        ),

        # IMPORTANT:
        # These are FLAT database fields.
        "headline": str(
            profile_data.get(
                "headline",
                ""
            ) or ""
        ),

        "about": str(
            profile_data.get(
                "about",
                ""
            ) or ""
        ),

        "department": str(
            profile_data.get(
                "department",
                student.get("department", "")
            ) or ""
        ),

        "degree": str(
            profile_data.get(
                "degree",
                "B.Tech"
            ) or "B.Tech"
        ),

        "graduation_year": str(
            profile_data.get(
                "graduation_year",
                ""
            ) or ""
        ),

        "college": str(
            profile_data.get(
                "college",
                ""
            ) or ""
        ),

        "cgpa": str(
            profile_data.get(
                "cgpa",
                ""
            ) or ""
        ),

        "skills": skills,

        "projects": projects,

        "certifications": certifications,

        "experience": experience,
    }

    return profile


# ============================================================
# PROFILE PAYLOAD
# ============================================================

def build_profile_payload(profile):

    graduation_year = profile.get(
        "graduation_year",
        None
    )

    cgpa = profile.get(
        "cgpa",
        None
    )

    # Convert empty values to None
    if graduation_year in [
        "",
        None
    ]:
        graduation_year = None
    else:
        try:
            graduation_year = int(
                graduation_year
            )
        except (
            ValueError,
            TypeError
        ):
            graduation_year = None

    if cgpa in [
        "",
        None
    ]:
        cgpa = None
    else:
        try:
            cgpa = float(
                cgpa
            )
        except (
            ValueError,
            TypeError
        ):
            cgpa = None

    payload = {

        "student_id": profile.get(
            "student_id",
            ""
        ),

        "full_name": profile.get(
            "full_name",
            ""
        ),

        "email": profile.get(
            "email",
            ""
        ),

        "phone": profile.get(
            "phone",
            ""
        ),

        "location": profile.get(
            "location",
            ""
        ),

        "headline": profile.get(
            "headline",
            ""
        ),

        "about": profile.get(
            "about",
            ""
        ),

        "department": profile.get(
            "department",
            ""
        ),

        "degree": profile.get(
            "degree",
            ""
        ),

        "graduation_year": graduation_year,

        "college": profile.get(
            "college",
            ""
        ),

        "cgpa": cgpa,

        "skills": profile.get(
            "skills",
            []
        ),

        "projects": profile.get(
            "projects",
            []
        ),

        "certifications": profile.get(
            "certifications",
            []
        ),

        "experience": profile.get(
            "experience",
            []
        ),
    }

    return payload


# ============================================================
# LOAD STUDENT PROFILE FROM FASTAPI
# ============================================================

def load_student_profile_from_api():

    api_client = get_api_client()

    try:

        response = (
            api_client.get_student_profile()
        )

        if response.status_code == 200:

            data = response.json()

            profile = normalize_profile(
                data
            )

            student_id = profile.get(
                "student_id"
            )

            st.session_state.student_profile = (
                profile
            )

            if student_id:

                st.session_state.student_profiles_by_id[
                    student_id
                ] = profile

            st.session_state.profile_loaded = True

            return profile

        if response.status_code == 404:

            student = (
                get_logged_in_student()
                or {}
            )

            profile = normalize_profile(
                {
                    "student_id":
                        student.get(
                            "student_id",
                            ""
                        )
                }
            )

            st.session_state.student_profile = (
                profile
            )

            st.session_state.profile_loaded = True

            return profile

        if response.status_code == 401:

            handle_session_expired()

            return {}

        try:

            detail = response.json().get(
                "detail",
                "Unable to load student profile."
            )

        except Exception:

            detail = (
                "Unable to load student profile."
            )

        st.warning(
            f"⚠️ {detail}"
        )

        return st.session_state.get(
            "student_profile",
            {}
        )

    except Exception as e:

        st.error(
            "❌ Unable to connect to the "
            "student profile API."
        )

        st.caption(
            f"Connection details: {e}"
        )

        return st.session_state.get(
            "student_profile",
            {}
        )


# ============================================================
# SAVE STUDENT PROFILE
# ============================================================

def save_student_profile_to_api(profile):

    api_client = get_api_client()

    payload = build_profile_payload(
        profile
    )

    try:

        response = (
            api_client.update_my_profile(
                payload
            )
        )

        if response.status_code in [
            200,
            201
        ]:

            try:

                saved_data = response.json()

                if isinstance(
                    saved_data,
                    dict
                ):

                    normalized = normalize_profile(
                        saved_data
                    )

                else:

                    normalized = profile

            except Exception:

                normalized = profile

            st.session_state.student_profile = (
                normalized
            )

            student_id = str(
                profile.get(
                    "student_id",
                    ""
                )
            )

            if student_id:

                st.session_state.student_profiles_by_id[
                    student_id
                ] = normalized

            return True, (
                "Profile saved successfully."
            )

        if response.status_code == 401:

            handle_session_expired()

            return False, (
                "Session expired."
            )

        try:

            detail = response.json().get(
                "detail",
                "Unable to save profile."
            )

        except Exception:

            detail = (
                "Unable to save profile."
            )

        return False, str(detail)

    except Exception as e:

        return False, (
            f"Unable to connect to API: {e}"
        )


# ============================================================
# SESSION EXPIRED
# ============================================================

def handle_session_expired():

    st.session_state.access_token = None

    st.session_state.student_logged_in = False

    st.session_state.logged_in_student = None

    st.session_state.profile_loaded = False

    if "api_client" in st.session_state:

        st.session_state.api_client.clear_token()

    st.warning(
        "🔐 Your session has expired. "
        "Please sign in again."
    )


# ============================================================
# JOB ID
# ============================================================

def get_job_id(job):

    # Live job ID
    live_job_id = job.get(
        "live_job_id"
    )

    if live_job_id is not None:

        return str(
            live_job_id
        )

    # Legacy job ID
    value = job.get(
        "job_id"
    )

    if value is None or str(
        value
    ).strip() == "":

        return (
            f"{job.get('company_name', '')}-"
            f"{job.get('role', '')}-"
            f"{job.get('location', '')}"
        )

    return str(value)


# ============================================================
# URL NORMALIZATION
# ============================================================

def normalize_url(url):

    if url is None:
        return ""

    url = str(url).strip()

    if url.lower() in {
        "",
        "nan",
        "none",
        "null"
    }:

        return ""

    if not (
        url.startswith("http://")
        or url.startswith("https://")
    ):

        url = (
            "https://"
            + url
        )

    return url


# ============================================================
# GET ALL JOBS FROM FASTAPI
# ============================================================

def get_all_jobs():

    api_client = get_api_client()

    try:

        response = api_client.get_jobs()

        if response.status_code == 401:

            handle_session_expired()

            return []

        if response.status_code != 200:

            try:

                detail = response.json().get(
                    "detail",
                    "Unable to load jobs."
                )

            except Exception:

                detail = (
                    "Unable to load jobs."
                )

            st.error(
                f"❌ {detail}"
            )

            return []

        data = response.json()

        if not isinstance(
            data,
            list
        ):

            st.error(
                "❌ Invalid job data received."
            )

            return []

        jobs = []

        for item in data:

            if not isinstance(
                item,
                dict
            ):
                continue

            job = dict(item)

            job["job_id"] = str(
                job.get(
                    "job_id",
                    ""
                )
            )

            job["company_name"] = str(
                job.get(
                    "company_name",
                    "Unknown Company"
                )
            )

            job["role"] = str(
                job.get(
                    "role",
                    job.get(
                        "job_title",
                        "Job Role"
                    )
                )
            )

            job["department"] = str(
                job.get(
                    "department",
                    "General"
                )
            )

            job["location"] = str(
                job.get(
                    "location",
                    "Not specified"
                )
            )

            job["salary"] = str(
                job.get(
                    "salary",
                    "Not specified"
                )
            )

            job["status"] = str(
                job.get(
                    "status",
                    "Open"
                )
            )

            job["application_url"] = (
                normalize_url(
                    job.get(
                        "application_url",
                        ""
                    )
                )
            )

            try:

                job["openings"] = int(
                    float(
                        job.get(
                            "openings",
                            0
                        )
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                job["openings"] = 0

            jobs.append(job)

        jobs.sort(
            key=lambda x: x.get(
                "openings",
                0
            ),
            reverse=True
        )

        return jobs

    except Exception as e:

        st.error(
            "❌ Unable to connect to "
            "Recruitment API."
        )

        st.caption(
            f"Connection details: {e}"
        )

        return []


# ============================================================
# ACTIVE JOB
# ============================================================

def is_active_job(job):

    status = str(
        job.get(
            "status",
            "Open"
        )
    ).strip().lower()

    return status in {
        "open",
        "active",
        "hiring",
        "ongoing",
        "available"
    }


# ============================================================
# SAVED JOB IDS
# ============================================================

def get_saved_job_ids():
    api_client = get_api_client()

    try:
        response = api_client.get_saved_jobs()

        if response.status_code == 401:
            return set()

        if response.status_code != 200:
            return set()

        data = response.json()

        if not isinstance(data, list):
            return set()

        result = set()

        for item in data:
            if not isinstance(item, dict):
                continue

            # Current live-job system
            live_job_id = item.get("live_job_id")

            if live_job_id is not None:
                result.add(str(live_job_id))
                continue

            # Legacy job support
            job_id = item.get("job_id")

            if job_id:
                result.add(str(live_job_id))

        return result

    except Exception:
        return set()


# ============================================================
# APPLICATION IDS
# ============================================================

def get_applied_job_ids():
    api_client = get_api_client()

    try:
        response = api_client.get_my_applications()

        if response.status_code == 401:
            return set()

        if response.status_code != 200:
            return set()

        data = response.json()

        if not isinstance(data, list):
            return set()

        job_ids = set()

        for item in data:
            if not isinstance(item, dict):
                continue

            # Current live-job application
            live_job_id = item.get("live_job_id")

            if live_job_id is not None:
                job_ids.add(str(live_job_id))
                continue

            # Legacy application support
            job_id = item.get("job_id")

            if job_id:
                job_ids.add(str(live_job_id))

        return job_ids

    except Exception:
        return set()


# ============================================================
# PROFILE COMPLETION
# ============================================================

def calculate_profile_completion():

    profile = st.session_state.get(
        "student_profile",
        {}
    )

    checks = [

        profile.get(
            "full_name"
        ),

        profile.get(
            "email"
        ),

        profile.get(
            "phone"
        ),

        profile.get(
            "location"
        ),

        profile.get(
            "headline"
        ),

        profile.get(
            "about"
        ),

        profile.get(
            "department"
        ),

        profile.get(
            "degree"
        ),

        profile.get(
            "college"
        ),

        profile.get(
            "graduation_year"
        ),

        profile.get(
            "cgpa"
        ),

        profile.get(
            "skills"
        ),

        profile.get(
            "projects"
        ),

        profile.get(
            "certifications"
        ),

        profile.get(
            "experience"
        ),

    ]

    completed = 0

    for value in checks:

        if isinstance(
            value,
            list
        ):

            if len(value) > 0:
                completed += 1

        elif value:

            completed += 1

    if not checks:
        return 0

    return int(
        completed /
        len(checks) *
        100
    )


# ============================================================
# LOGIN
# ============================================================

def student_login():

    st.markdown(
        """
        <h1 style="text-align:center;">
            🎓 Student Portal
        </h1>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style="
            text-align:center;
            color:#9aa1b2;
        ">
        Find jobs, discover opportunities
        and manage your career.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    left, center, right = st.columns(
        [1, 1.25, 1]
    )

    with center:

        tab1, tab2, tab3 = st.tabs(
            [
                "🔐 Sign In",
                "📝 Create Account",
                "🔑 Forgot Password"
            ]
        )

        # ====================================================
        # SIGN IN
        # ====================================================

        with tab1:

            st.subheader(
                "Welcome Back 👋"
            )

            username = st.text_input(
                "📧 Username or Email",
                placeholder=(
                    "Enter username or email"
                ),
                key="student_login_username"
            )

            password = st.text_input(
                "🔒 Password",
                type="password",
                placeholder=(
                    "Enter password"
                ),
                key="student_login_password"
            )

            if st.button(
                "🔐 Sign In",
                type="primary",
                use_container_width=True,
                key="student_signin_button"
            ):

                username_input = username.strip()
                password_input = password.strip()

                if not username_input:
                    st.error(
                        "❌ Enter your username or email."
                    )
                    return

                if not password_input:
                    st.error(
                        "❌ Enter your password."
                    )
                    return

                try:

                    api_client = get_api_client()

                    response = api_client.login(
                        username_input,
                        password_input
                    )
                

                    # ====================================================
                    # LOGIN SUCCESS
                    # ====================================================

                    if response.status_code == 200:

                        data = response.json()

                        access_token = data.get(
                            "access_token"
                        )

                        if not access_token:
                            st.error(
                                "❌ Login response did not contain an access token."
                            )
                            return

                        api_client.set_token(
                            access_token
                        )

                        student_data = {
                            "student_id": str(
                                data.get(
                                    "student_id",
                                    ""
                                )
                            ),
                            "student_name": str(
                                data.get(
                                    "student_name",
                                    ""
                                )
                            ),
                            "username": str(
                                data.get(
                                    "username",
                                    ""
                                )
                            ),
                            "email": str(
                                data.get(
                                    "email",
                                    ""
                                )
                            ),
                            "department": str(
                                data.get(
                                    "department",
                                    ""
                                )
                            ),
                        }

                        # ------------------------------------------------
                        # SAVE LOGIN SESSION
                        # ------------------------------------------------

                        st.session_state.access_token = (
                            access_token
                        )

                        st.session_state.api_client = (
                            api_client
                        )

                        st.session_state.logged_in_student = (
                            student_data
                        )

                        st.session_state.student_logged_in = (
                            True
                        )

                        # ------------------------------------------------
                        # LOAD STUDENT PROFILE
                        # ------------------------------------------------

                        profile = (
                            load_student_profile_from_api()
                        )

                        if not profile:

                            profile = normalize_profile(
                                {
                                    "student_id":
                                        student_data[
                                            "student_id"
                                        ]
                                }
                            )

                        st.session_state.student_profile = (
                            profile
                        )

                        # ------------------------------------------------
                        # RESET APPLICATION FORM
                        # ------------------------------------------------

                        st.session_state.show_application_form = (
                            False
                        )

                        st.session_state.selected_application_job = (
                            None
                        )

                        st.session_state.student_page = (
                            "Dashboard"
                        )

                        st.success(
                            "✅ Login successful."
                        )

                        st.rerun()

                    # ====================================================
                    # INVALID LOGIN
                    # ====================================================

                    elif response.status_code == 401:

                        st.error(
                            "❌ Invalid username/email or password."
                        )

                    # ====================================================
                    # VALIDATION ERROR
                    # ====================================================

                    elif response.status_code == 422:

                        st.error(
                            "❌ Please enter valid login details."
                        )

                    # ====================================================
                    # OTHER API ERROR
                    # ====================================================

                    else:

                        try:

                            detail = response.json().get(
                                "detail",
                                "Unable to login."
                            )

                        except Exception:

                            detail = (
                                "Unable to login."
                            )

                        st.error(
                            f"❌ {detail}"
                        )

                # ========================================================
                # PYTHON / NETWORK ERROR
                # ========================================================

                except Exception as e:

                    st.error(
                        f"❌ Login failed: {e}"
                    )
        # ====================================================
        # CREATE ACCOUNT
        # ====================================================

        with tab2:

            st.subheader(
                "Create Your Account 🚀"
            )

            name = st.text_input(
                "👤 Full Name",
                key="signup_name"
            )

            email = st.text_input(
                "📧 Email",
                key="signup_email"
            )

            username = st.text_input(
                "👨‍💻 Username",
                key="signup_username"
            )

            department = st.selectbox(
                "🎓 Department",
                [
                    "CSE",
                    "ECE",
                    "EEE",
                    "MECH",
                    "CIVIL",
                    "Data Science",
                    "AI & ML",
                    "Other"
                ],
                key="signup_department"
            )

            password = st.text_input(
                "🔒 Password",
                type="password",
                key="signup_password"
            )

            confirm = st.text_input(
                "🔒 Confirm Password",
                type="password",
                key="signup_confirm"
            )

            # ------------------------------------------------
            # STEP 1: SEND OTP
            # ------------------------------------------------

            if not st.session_state.get(
                "signup_otp_sent",
                False
            ):

                if st.button(
                    "📧 Send OTP",
                    type="primary",
                    use_container_width=True,
                    key="send_signup_otp"
                ):

                    if not name.strip():
                        st.error("Enter your full name.")

                    elif not email.strip():
                        st.error("Enter your email.")

                    elif not username.strip():
                        st.error("Choose a username.")

                    elif len(password) < 6:
                        st.error(
                            "Password must contain at least 6 characters."
                        )

                    elif password != confirm:
                        st.error(
                            "Passwords do not match."
                        )

                    else:

                        try:

                            response = requests.post(
                               f"{API_BASE_URL}/students/register/request-otp",
                                params={
                                    "email": email.strip()
                                },
                                timeout=15
                            )

                            if response.status_code == 200:

                                st.session_state[
                                    "signup_otp_sent"
                                ] = True

                                st.success(
                                    "OTP sent successfully. "
                                    "Check your email."
                                )

                                st.rerun()

                            else:

                                try:
                                    detail = response.json().get(
                                        "detail",
                                        "Unable to send OTP."
                                    )
                                except Exception:
                                    detail = "Unable to send OTP."

                                st.error(detail)

                        except Exception as e:

                            st.error(
                                f"Unable to connect to server: {e}"
                            )

            # ------------------------------------------------
            # STEP 2: VERIFY OTP + CREATE ACCOUNT
            # ------------------------------------------------

            else:

                st.success(
                    "OTP sent to your email."
                )

                otp = st.text_input(
                    "🔐 Enter OTP",
                    max_chars=6,
                    key="signup_otp"
                )

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "✅ Verify & Create Account",
                        type="primary",
                        use_container_width=True,
                        key="verify_signup_otp"
                    ):

                        if not otp.strip():

                            st.error(
                                "Enter the OTP."
                            )

                        else:

                            try:

                                response = requests.post(
                                   f"{API_BASE_URL}/students/register",
                                    params={
                                        "student_name": name.strip(),
                                        "username": username.strip(),
                                        "email": email.strip(),
                                        "department": department,
                                        "password": password,
                                        "otp": otp.strip()
                                    },
                                    timeout=15
                                )

                                if response.status_code == 200:

                                    data = response.json()

                                    st.success(
                                        "🎉 Account created successfully!"
                                    )

                                    st.info(
                                        "You can now sign in with "
                                        "your username and password."
                                    )

                                    # Reset registration state
                                    st.session_state[
                                        "signup_otp_sent"
                                    ] = False

                                    
                                else:

                                    try:
                                        detail = response.json().get(
                                            "detail",
                                            "Account creation failed."
                                        )
                                    except Exception:
                                        detail = "Account creation failed."

                                    st.error(detail)

                            except Exception as e:

                                st.error(
                                    f"Unable to connect to server: {e}"
                                )

                with col2:

                    if st.button(
                        "🔄 Start Again",
                        use_container_width=True,
                        key="restart_signup"
                    ):

                        st.session_state[
                            "signup_otp_sent"
                        ] = False

                        st.rerun()

        # ====================================================
        # FORGOT PASSWORD
        # ====================================================

        with tab3:

            st.subheader(
                "Reset Password 🔑"
            )

            reset_email = st.text_input(
                "📧 Registered Email",
                key="reset_email"
            )

            # ------------------------------------------------
            # STEP 1: SEND OTP
            # ------------------------------------------------

            if not st.session_state.get(
                "reset_otp_sent",
                False
            ):

                if st.button(
                    "📧 Send Reset OTP",
                    type="primary",
                    use_container_width=True,
                    key="send_reset_otp"
                ):

                    if not reset_email.strip():

                        st.error(
                            "Enter your registered email."
                        )

                    else:

                        try:

                            response = requests.post(
                               f"{API_BASE_URL}/students/forgot-password/request-otp",
                                params={
                                    "email": reset_email.strip()
                                },
                                timeout=15
                            )

                            if response.status_code == 200:

                                st.session_state[
                                    "reset_otp_sent"
                                ] = True

                                st.success(
                                    "OTP sent successfully. "
                                    "Check your email."
                                )

                                st.rerun()

                            else:

                                try:
                                    detail = response.json().get(
                                        "detail",
                                        "Unable to send OTP."
                                    )
                                except Exception:
                                    detail = "Unable to send OTP."

                                st.error(detail)

                        except Exception as e:

                            st.error(
                                f"Unable to connect to server: {e}"
                            )

            # ------------------------------------------------
            # STEP 2: OTP + NEW PASSWORD
            # ------------------------------------------------

            else:

                st.success(
                    "OTP sent to your registered email."
                )

                otp = st.text_input(
                    "🔐 Enter OTP",
                    max_chars=6,
                    key="reset_otp"
                )

                new_password = st.text_input(
                    "🔒 New Password",
                    type="password",
                    key="reset_password"
                )

                confirm_password = st.text_input(
                    "🔒 Confirm New Password",
                    type="password",
                    key="reset_confirm_password"
                )

                if st.button(
                    "🔑 Verify OTP & Reset Password",
                    type="primary",
                    use_container_width=True,
                    key="reset_password_button"
                ):

                    if not otp.strip():

                        st.error(
                            "Enter the OTP."
                        )

                    elif len(new_password) < 6:

                        st.error(
                            "Password must contain at least 6 characters."
                        )

                    elif new_password != confirm_password:

                        st.error(
                            "Passwords do not match."
                        )

                    else:

                        try:

                            response = requests.post(
                               f"{API_BASE_URL}/students/forgot-password/reset",
                                params={
                                    "email": reset_email.strip(),
                                    "otp": otp.strip(),
                                    "new_password": new_password
                                },
                                timeout=15
                            )

                            if response.status_code == 200:

                                st.success(
                                    "🎉 Password reset successfully!"
                                )

                                st.info(
                                    "You can now sign in using "
                                    "your new password."
                                )

                                st.session_state[
                                    "reset_otp_sent"
                                ] = False

                              

                            else:

                                try:
                                    detail = response.json().get(
                                        "detail",
                                        "Password reset failed."
                                    )
                                except Exception:
                                    detail = "Password reset failed."

                                st.error(detail)

                        except Exception as e:

                            st.error(
                                f"Unable to connect to server: {e}"
                            )

                if st.button(
                    "🔄 Start Again",
                    use_container_width=True,
                    key="restart_reset"
                ):

                    st.session_state[
                        "reset_otp_sent"
                    ] = False

                    st.rerun()

# ============================================================
# DASHBOARD
# ============================================================

def dashboard_page():
    student = get_logged_in_student()

    if not student:
        return

    profile = st.session_state.get(
        "student_profile",
        {}
    )

    completion = calculate_profile_completion()

    saved_job_ids = get_saved_job_ids()

    applied_job_ids = get_applied_job_ids()

    skills = profile.get(
        "skills",
        []
    )

    st.title(
        f"Welcome back, "
        f"{student.get('student_name', 'Student')} 👋"
    )

   

    # ========================================================
    # METRICS
    # ========================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Profile Completion",
            f"{completion}%"
        )

    with col2:

        st.metric(
            "Saved Jobs",
            len(saved_job_ids)
        )

    with col3:

        st.metric(
            "Applications",
            len(applied_job_ids)
        )

    with col4:

        st.metric(
            "Skills",
            len(skills)
        )

    st.divider()

    # ========================================================
    # PROFILE COMPLETION
    # ========================================================

    st.subheader(
        "🚀 Complete Your Profile"
    )

    st.progress(
        completion / 100
    )

    if completion < 100:

        st.info(
            "Complete your profile to improve "
            "personalized job recommendations."
        )

    else:

        st.success(
            "🎉 Your profile is complete!"
        )

    st.divider()

    # ========================================================
    # PROFILE SUMMARY
    # ========================================================

    st.subheader(
        "👤 Profile Summary"
    )

    c1, c2 = st.columns(2)

    with c1:

        st.write(
            f"**Name:** "
            f"{profile.get('full_name', student.get('student_name', '-'))}"
        )

        st.write(
            f"**Email:** "
            f"{profile.get('email', student.get('email', '-'))}"
        )

        st.write(
            f"**Department:** "
            f"{profile.get('department', student.get('department', '-'))}"
        )

        st.write(
            f"**Location:** "
            f"{profile.get('location', '-')}"
        )

    # with c2:
    #     if st.button(
    #         "🗑️ Remove",
    #         key=f"saved_remove_{job_id}",
    #         use_container_width=True
    #     ):
    #         live_job_id = job.get("live_job_id")

    #         if live_job_id is None:
    #             st.error(
    #                 "Unable to remove saved job: "
    #                 "Live job ID is missing."
    #             )
    #         else:
    #             try:
    #                 response = api_client.delete_saved_job(
    #                     live_job_id=int(live_job_id)
    #                 )

    #                 if response.status_code in [200, 204]:
    #                     st.success(
    #                         "Job removed from saved jobs."
    #                     )
    #                     st.rerun()

    #                 elif response.status_code == 401:
    #                     handle_session_expired()

    #                 else:
    #                     st.error(
    #                         f"Unable to remove saved job. "
    #                         f"Status: {response.status_code}"
    #                     )

    #             except Exception as e:
    #                 st.error(
    #                     f"Failed to remove saved job: {e}"
    #                 )
    # ========================================================
    # QUICK ACTIONS
    # ========================================================

    st.subheader(
        "⚡ Quick Actions"
    )

    q1, q2, q3, q4 = st.columns(4)

    with q1:

        if st.button(
            "🔎 Find Jobs",
            use_container_width=True,
            key="quick_find_jobs"
        ):

            st.session_state.student_page = (
                "Find Jobs"
            )

            st.rerun()

    with q2:

        if st.button(
            "⭐ Recommended",
            use_container_width=True,
            key="quick_recommended_jobs"
        ):

            st.session_state.student_page = (
                "Recommended Jobs"
            )

            st.rerun()

    with q3:

        if st.button(
            "🔮 Future Hiring",
            use_container_width=True,
            key="quick_future_hiring"
        ):

            st.session_state.student_page = (
                "Future Hiring"
            )

            st.rerun()

    with q4:

        if st.button(
            "👤 Edit Profile",
            use_container_width=True,
            key="quick_edit_profile"
        ):

            st.session_state.student_page = (
                "My Profile"
            )

            st.rerun()


# ============================================================
# APPLICATION FORM
# ============================================================

def application_form_page():

    job = st.session_state.get(
        "selected_application_job"
    )

    if not job:

        st.error(
            "No job selected."
        )

        st.session_state.show_application_form = (
            False
        )

        return

    api_client = get_api_client()

    student = get_logged_in_student() or {}

    live_job_id = job.get("live_job_id")

    st.title(
        "🚀 Apply for Job"
    )

    st.caption(
        "Submit your application through the recruitment portal."
    )

    st.divider()

    st.subheader(
        job.get(
            "role",
            "Job Role"
        )
    )

    st.write(
        f"🏢 **{job.get('company_name', 'Company')}**"
    )

    st.caption(
        f"🎓 {job.get('department', '-')}"
        f" • 📍 {job.get('location', '-')}"
    )

    st.divider()

    # ========================================================
    # STUDENT DETAILS
    # ========================================================

    st.subheader(
        "👤 Applicant Details"
    )

    c1, c2 = st.columns(2)

    with c1:

        st.text_input(
            "Full Name",
            value=student.get(
                "student_name",
                ""
            ),
            disabled=True,
            key="application_name"
        )

    with c2:

        st.text_input(
            "Student ID",
            value=student.get(
                "student_id",
                ""
            ),
            disabled=True,
            key="application_student_id"
        )

    st.text_input(
        "Email",
        value=student.get(
            "email",
            ""
        ),
        disabled=True,
        key="application_email"
    )

    # ========================================================
    # RESUME
    # ========================================================

    st.subheader(
        "📄 Resume *"
    )

    profile_resume = st.session_state.get(
        "student_resume"
    )

    resume_filename = None

    if profile_resume:

        resume_filename = (
            profile_resume.get(
                "name"
            )
        )

        st.success(
            f"Using uploaded resume: "
            f"**{resume_filename}**"
        )

    else:

        resume = st.file_uploader(
            "Upload Resume",
            type=[
                "pdf",
                "doc",
                "docx"
            ],
            key="application_resume_upload"
        )

        if resume:

            resume_filename = (
                resume.name
            )

            st.session_state.student_resume = {

                "name":
                    resume.name,

                "type":
                    resume.type,

                "size":
                    resume.size,

                "data":
                    resume.getvalue()

            }

    # ========================================================
    # COVER LETTER
    # ========================================================

    cover_letter = st.text_area(
        "Cover Letter / Application Message",
        height=180,
        placeholder=(
            "Write a short professional message "
            "for the company..."
        ),
        key="application_cover_letter"
    )

    confirmation = st.checkbox(
        "I confirm that the information provided is correct.",
        key="application_confirmation"
    )

    st.divider()

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "← Cancel",
            use_container_width=True,
            key="cancel_application"
        ):

            st.session_state.show_application_form = (
                False
            )

            st.session_state.selected_application_job = (
                None
            )

            st.rerun()

    with c2:

        if st.button(
            "🚀 Submit Application",
            type="primary",
            use_container_width=True,
            key="submit_application"
        ):

            if not confirmation:

                st.warning(
                    "Please confirm the application information."
                )

                return
            if not resume_filename:

               st.error(
                "❌ Resume is mandatory. Please upload your resume."
    )

               return

            try:

               # ------------------------------------------------
                # UPLOAD RESUME TO BACKEND
                # ------------------------------------------------

                profile_resume = st.session_state.get("student_resume")

                if not profile_resume or not profile_resume.get("data"):
                    st.error("❌ Resume file data is not available. Please upload your resume again.")
                    return

                resume_upload_response = api_client.upload_resume(
                    file_name=profile_resume.get("name", resume_filename),
                    file_data=profile_resume.get("data"),
                    mime_type=profile_resume.get(
                        "type",
                        "application/octet-stream"
                    )
                )

                if resume_upload_response.status_code not in (200, 201):
                    try:
                        detail = resume_upload_response.json().get(
                            "detail",
                            "Resume upload failed."
                        )
                    except Exception:
                        detail = "Resume upload failed."

                    st.error(f"❌ {detail}")
                    return

                resume_data = resume_upload_response.json()

                resume_id = resume_data.get("resume_id")

                if not resume_id:
                    st.error("❌ Resume uploaded but resume ID was not returned.")
                    return

                # ------------------------------------------------
                # SUBMIT APPLICATION
                # ------------------------------------------------

                # ---------------------------------------------------------
                # UPLOAD RESUME TO SERVER
                # ---------------------------------------------------------
                api_client = get_api_client()

                profile_resume = st.session_state.get("student_resume")

                if not profile_resume:
                    st.error("Please upload a resume before applying.")
                    return

                resume_upload_response = api_client.upload_resume(
                    file_name=profile_resume["name"],
                    file_data=profile_resume["data"],
                    mime_type=profile_resume.get("type")
                )

                if resume_upload_response.status_code not in (200, 201):
                    st.error(
                        f"Resume upload failed: "
                        f"{resume_upload_response.text}"
                    )
                    return

                resume_data = resume_upload_response.json()
                resume_id = resume_data.get("resume_id")

                if not resume_id:
                    st.error("Resume upload succeeded but no resume ID was returned.")
                    return

                # ---------------------------------------------------------
                # SUBMIT APPLICATION
                # ---------------------------------------------------------
                response = api_client.apply_for_job(
                    job_id=None,
                    live_job_id=int(live_job_id),
                    cover_letter=(cover_letter.strip() if cover_letter else None),
                    resume_filename=resume_filename,
                    resume_id=resume_id
                )
                

                if response.status_code in [
                        200,
                        201
                    ]:

                    application_data = response.json()

                    st.session_state.application_success = {
                        "application_id": application_data.get(
                            "application_id",
                            application_data.get("id", "-")
                        ),
                        "company": application_data.get(
                            "company_name",
                            "-"
                        ),
                        "role": application_data.get(
                            "job_title",
                            "-"
                        ),
                        "live_job_id": application_data.get(
                            "live_job_id",
                            "-"
                        ),
                        "source": application_data.get(
                            "source",
                            "-"
                        ),
                        "status": application_data.get(
                            "status",
                            "Applied"
                        )
                    }

                    st.session_state.show_application_form = (
                        False
                    )

                    st.session_state.selected_application_job = (
                        None
                    )

                    st.success(
                        "🎉 Application submitted successfully!"
                    )

                    st.info(
                        "Your application is now available "
                        "in My Applications."
                    )

                    st.session_state.student_page = (
                        "My Applications"
                    )

                    st.rerun()

                elif response.status_code == 400:

                    try:

                        detail = (
                            response.json().get(
                                "detail",
                                "You have already applied."
                            )
                        )

                    except Exception:

                        detail = (
                            "You have already applied."
                        )

                    st.warning(
                        f"⚠️ {detail}"
                    )

                elif response.status_code == 401:

                    handle_session_expired()

                elif response.status_code == 404:

                    st.error(
                        "❌ Job not found."
                    )

                else:

                    try:

                        detail = (
                            response.json().get(
                                "detail",
                                "Unable to submit application."
                            )
                        )

                    except Exception:

                        detail = (
                            "Unable to submit application."
                        )

                    st.error(
                        f"❌ {detail}"
                    )

            except Exception as e:

                st.error(
                    "❌ Unable to submit application."
                )

                st.caption(
                    f"Connection details: {e}"
                )


# ============================================================
# FIND JOBS
# ============================================================

def find_jobs_page():

    st.title(
        "🔎 Find Jobs"
    )

    st.caption(
        "Discover current live openings and apply through the portal."
    )

    jobs = [
        job
        for job in get_all_jobs()
        if is_active_job(job)
    ]

    if not jobs:

        st.warning(
            "No active jobs are currently available."
        )

        return

    # ========================================================
    # FILTERS
    # ========================================================

    st.subheader(
        "🎯 Search & Filters"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        search = st.text_input(
            "🔍 Search",
            placeholder=(
                "Company, role, skill or location..."
            ),
            key="find_jobs_search"
        )

    with c2:

        departments = sorted(
            {
                str(
                    job.get(
                        "department",
                        ""
                    )
                )
                for job in jobs
                if job.get(
                    "department"
                )
            }
        )

        selected_department = st.selectbox(
            "🏫 Department",
            [
                "All Departments"
            ] + departments,
            key="find_jobs_department"
        )

    with c3:

        locations = sorted(
            {
                str(
                    job.get(
                        "location",
                        ""
                    )
                )
                for job in jobs
                if job.get(
                    "location"
                )
            }
        )

        selected_location = st.selectbox(
            "📍 Location",
            [
                "All Locations"
            ] + locations,
            key="find_jobs_location"
        )

    # ========================================================
    # FILTER JOBS
    # ========================================================

    filtered = []

    search_value = (
        search.strip().lower()
    )

    for job in jobs:

        searchable = " ".join(
            [
                str(
                    job.get(
                        "company_name",
                        ""
                    )
                ),

                str(
                    job.get(
                        "role",
                        ""
                    )
                ),

                str(
                    job.get(
                        "department",
                        ""
                    )
                ),

                str(
                    job.get(
                        "location",
                        ""
                    )
                ),

                str(
                    job.get(
                        "skills",
                        ""
                    )
                ),

            ]
        ).lower()

        if search_value:

            if search_value not in searchable:
                continue

        if (
            selected_department
            != "All Departments"
        ):

            if str(
                job.get(
                    "department",
                    ""
                )
            ) != selected_department:

                continue

        if (
            selected_location
            != "All Locations"
        ):

            if str(
                job.get(
                    "location",
                    ""
                )
            ) != selected_location:

                continue

        filtered.append(job)

    # ========================================================
    # METRICS
    # ========================================================

    st.divider()

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Open Roles",
            len(filtered)
        )

    with c2:

        st.metric(
            "Current Openings",
            sum(
                int(
                    job.get(
                        "openings",
                        0
                    )
                )
                for job in filtered
            )
        )

    with c3:

        st.metric(
            "Companies",
            len(
                {
                    job.get(
                        "company_name"
                    )
                    for job in filtered
                }
            )
        )

    st.divider()

    st.subheader(
        f"🚀 Current Opportunities ({len(filtered)})"
    )

    if not filtered:

        st.info(
            "No jobs match your search."
        )

        return

    # ========================================================
    # API STATE
    # ========================================================

    api_client = get_api_client()

    saved_job_ids = (
        get_saved_job_ids()
    )

    applied_job_ids = (
        get_applied_job_ids()
    )

    # ========================================================
    # JOB CARDS
    # ========================================================

    for job in filtered:

        live_job_id = job.get("live_job_id")

        company = str(
            job.get(
                "company_name",
                "Company"
            )
        )

        role = str(
            job.get(
                "role",
                "Job Role"
            )
        )

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

        openings = int(
            job.get(
                "openings",
                0
            )
        )

        official_url = normalize_url(
            job.get(
                "application_url",
                ""
            )
        )

        saved = (
            str(live_job_id)
            in saved_job_ids
        )

        applied = (
            str(live_job_id)
            in applied_job_ids
        )

        with st.container(
            border=True
        ):

            c1, c2 = st.columns(
                [4, 1]
            )

            with c1:

                st.markdown(
                    f"### 💼 {role}"
                )

                st.write(
                    f"🏢 **{company}**"
                )

            with c2:

                st.metric(
                    "Openings",
                    openings
                )

            st.caption(
                f"🎓 {department}"
                f" • 📍 {location}"
                f" • 💰 {salary}"
            )

            # ------------------------------------------------
            # SKILLS
            # ------------------------------------------------

            skills = job.get(
                "skills",
                ""
            )

            if skills:

                st.write(
                    f"🛠️ **Skills:** {skills}"
                )

            st.divider()

            a, b, c = st.columns(3)

            # ------------------------------------------------
            # SAVE
            # ------------------------------------------------

            with a:

                if saved:

                    if st.button(
                        "🔖 Remove Saved",
                        key=f"remove_saved_{live_job_id}",
                        use_container_width=True
                    ):

                        live_job_id = job.get("id")

                        if live_job_id is None:
                            st.error("Unable to remove saved job: Live job ID is missing.")
                        else:
                            response = api_client.delete_saved_job(
                                live_job_id=int(live_job_id)
                            )

                        if response.status_code in [
                            200,
                            204
                        ]:

                            st.success(
                                "Job removed from saved jobs."
                            )

                            st.rerun()

                        elif response.status_code == 401:

                            handle_session_expired()

                        else:

                            st.error(
                                "Unable to remove saved job."
                            )

                else:
                    if st.button(
                        "🔖 Save Job",
                        key=f"save_job_{live_job_id}",
                        use_container_width=True
                    ):
                        live_job_id = job.get("id")

                        if live_job_id is None:
                            st.error(
                                "Unable to save job: "
                                "Live Job ID is missing."
                            )
                        else:
                            try:
                                response = api_client.save_job(
                                    live_job_id=int(live_job_id)
                                )

                                if response.status_code in [200, 201]:
                                    st.success("Job saved!")
                                    st.rerun()

                                elif response.status_code == 400:
                                    try:
                                        detail = response.json().get(
                                            "detail",
                                            "Job is already saved."
                                        )
                                    except Exception:
                                        detail = "Job is already saved."

                                    st.warning(str(detail))

                                elif response.status_code == 401:
                                    handle_session_expired()

                                else:
                                    try:
                                        detail = response.json().get(
                                            "detail",
                                            "No error detail returned."
                                        )
                                    except Exception:
                                        detail = response.text

                                    st.error(
                                        f"❌ Unable to save job. "
                                        f"Status: {response.status_code}"
                                    )

                                    st.code(
                                        str(detail)
                                    )
                                    
                            except Exception as e:
                                        st.error(
                                        f"❌ Unable to save this job: {e}"
                                        )
            # ------------------------------------------------
            # APPLY
            # ------------------------------------------------

            with b:

                if applied:

                    st.button(
                        "✅ Applied",
                        disabled=True,
                        key=f"already_applied_{live_job_id}",
                        use_container_width=True
                    )

                else:

                    if st.button(
                        "🚀 Apply Now",
                        key=f"apply_job_{live_job_id}",
                        type="primary",
                        use_container_width=True
                    ):

                        st.session_state.selected_application_job = (
                            job
                        )

                        st.session_state.show_application_form = (
                            True
                        )

                        st.rerun()

            # ------------------------------------------------
            # OFFICIAL WEBSITE
            # ------------------------------------------------

            with c:

                if official_url:

                    st.link_button(
                        "🌐 Official Website",
                        official_url,
                        use_container_width=True
                    )

                else:

                    st.caption(
                        "Official link unavailable"
                    )


# ============================================================
# SAVED JOBS
# ============================================================

def saved_jobs_page():

    st.title(
        "🔖 Saved Jobs"
    )

    st.caption(
        "Jobs saved by you are stored in PostgreSQL."
    )

    api_client = get_api_client()

    response = (
        api_client.get_saved_jobs()
    )

    if response.status_code == 401:

        handle_session_expired()

        return

    if response.status_code != 200:

        st.error(
            f"Unable to load saved jobs. "
            f"Status: {response.status_code}"
        )

        return

    records = response.json()
  

    if not records:

        st.info(
            "You have not saved any jobs yet."
        )

        st.write(
            "Go to **Find Jobs** and save jobs you are interested in."
        )

        return

    saved_jobs = []

    for record in records:

        if not isinstance(
            record,
            dict
        ):
            continue

        # --------------------------------------------------------
        # LIVE SAVED JOB
        # --------------------------------------------------------

        live_job_id = record.get(
            "live_job_id"
        )

        if live_job_id is not None:

            try:

                live_job_id = int(
                    live_job_id
                )

            except (
                ValueError,
                TypeError
            ):

                continue

            # Get live job through API client
            live_job_response = api_client.get_live_job(live_job_id)

            if live_job_response.status_code == 200:

                job = live_job_response.json()

                if isinstance(job, dict):

                    job["saved_record_id"] = (
                        record.get("saved_job_id")
                    )

                    job["live_job_id"] = live_job_id

                    saved_jobs.append(job)

            continue

        # --------------------------------------------------------
        # LEGACY SAVED JOB
        # --------------------------------------------------------
        # Legacy jobs use job_id and are no longer supported.
        # Only live_job_id records are displayed.
        continue

    if not saved_jobs:

        st.info(
            "Saved jobs are no longer available."
        )

        return

    st.write(
        f"### {len(saved_jobs)} Saved Opportunity(s)"
    )

    applied_job_ids = (
        get_applied_job_ids()
    )

    for job in saved_jobs:

        live_job_id = job.get("live_job_id")

        if live_job_id is None:
            continue

        try:
            live_job_id = int(live_job_id)
        except (ValueError, TypeError):
            continue

       

        with st.container(
            border=True
        ):

            st.subheader(
                job.get(
                    "role",
                    "Job Role"
                )
            )

            st.write(
                f"🏢 **{job.get('company_name', 'Company')}**"
            )

            st.caption(
                f"📍 {job.get('location', '-')}"
                f" • 💰 {job.get('salary', '-')}"
                f" • 🎓 {job.get('department', '-')}"
            )

            c1, c2 = st.columns(2)

            with c1:

                if str(live_job_id) in applied_job_ids:

                    st.button(
                        "✅ Applied",
                        disabled=True,
                        key=f"saved_already_applied_{live_job_id}",
                        use_container_width=True
                    )

                else:

                    if st.button(
                        "🚀 Apply Now",
                        type="primary",
                        key=f"saved_apply_{live_job_id}",
                        use_container_width=True
                    ):

                        st.session_state.selected_application_job = (
                            job
                        )

                        st.session_state.show_application_form = (
                            True
                        )

                        st.rerun()

            with c2:

                if st.button(
                    "🗑️ Remove",
                    key=f"saved_remove_{live_job_id}",
                    use_container_width=True
                ):

                    live_job_id = job.get(
                        "live_job_id"
                    )

                    if live_job_id is None:

                        st.error(
                            "Unable to remove saved job: "
                            "Live job ID is missing."
                        )

                    else:

                        try:

                            response = api_client.delete_saved_job(
                                live_job_id=int(live_job_id)
                            )

                            if response.status_code in [
                                200,
                                204
                            ]:

                                st.success(
                                    "Job removed from saved jobs."
                                )

                                st.rerun()

                            elif response.status_code == 401:

                                handle_session_expired()

                            else:

                                st.error(
                                    f"Unable to remove saved job. "
                                    f"Status: {response.status_code}"
                                )

                        except Exception as e:

                            st.error(
                                f"Failed to remove saved job: {e}"
             
                       )


# ============================================================
# ROLE INTELLIGENCE
# ============================================================

def role_intelligence_page():

    st.title(
        "💼 Role Intelligence"
    )

    st.caption(
        "Analyze current openings by department, role and month."
    )

    jobs = [
        job
        for job in get_all_jobs()
        if is_active_job(job)
    ]

    if not jobs:

        st.warning(
            "No current openings available."
        )

        return

    # ========================================================
    # FILTERS
    # ========================================================

    c1, c2, c3 = st.columns(3)

    departments = sorted(
        {
            str(
                job.get(
                    "department",
                    ""
                )
            )
            for job in jobs
            if job.get(
                "department"
            )
        }
    )

    roles = sorted(
        {
            str(
                job.get(
                    "role",
                    ""
                )
            )
            for job in jobs
            if job.get(
                "role"
            )
        }
    )

    with c1:

        selected_department = st.selectbox(
            "🎓 Department",
            [
                "All Departments"
            ] + departments,
            key="role_intelligence_department"
        )

    with c2:

        selected_role = st.selectbox(
            "💼 Role",
            [
                "All Roles"
            ] + roles,
            key="role_intelligence_role"
        )

    with c3:

        month_filter = st.selectbox(
            "📅 Month",
            [
                "All Months",
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
            ],
            key="role_intelligence_month"
        )

    # ========================================================
    # FILTER
    # ========================================================

    filtered = []

    for job in jobs:

        if (
            selected_department
            != "All Departments"
        ):

            if str(
                job.get(
                    "department",
                    ""
                )
            ) != selected_department:

                continue

        if (
            selected_role
            != "All Roles"
        ):

            if str(
                job.get(
                    "role",
                    ""
                )
            ) != selected_role:

                continue

        # ----------------------------------------------------
        # Month filtering
        # ----------------------------------------------------

        if month_filter != "All Months":

            posted_value = (
                job.get(
                    "posted_date",
                    ""
                )
            )

            if posted_value:

                if month_filter.lower() not in str(
                    posted_value
                ).lower():

                    continue

        filtered.append(job)

    # ========================================================
    # SUMMARY
    # ========================================================

    st.divider()

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Matching Roles",
            len(filtered)
        )

    with c2:

        st.metric(
            "Openings",
            sum(
                int(
                    job.get(
                        "openings",
                        0
                    )
                )
                for job in filtered
            )
        )

    with c3:

        st.metric(
            "Companies",
            len(
                {
                    job.get(
                        "company_name"
                    )
                    for job in filtered
                }
            )
        )

    st.divider()

    if not filtered:

        st.info(
            "No openings match the selected filters."
        )

        return

    st.subheader(
        f"🚀 Matching Current Openings ({len(filtered)})"
    )

    applied_ids = (
        get_applied_job_ids()
    )

    for job in filtered:

        live_job_id = job.get("live_job_id")

        with st.container(
            border=True
        ):

            st.markdown(
                f"### 💼 {job.get('role', 'Job Role')}"
            )

            st.write(
                f"🏢 **{job.get('company_name', '-') }**"
            )

            st.caption(
                f"🎓 {job.get('department', '-')}"
                f" • 📍 {job.get('location', '-')}"
                f" • 💰 {job.get('salary', '-')}"
            )

            if job.get(
                "posted_date"
            ):

                st.caption(
                    f"📅 Posted: "
                    f"{job.get('posted_date')}"
                )

            if str(live_job_id) in applied_ids:

                st.button(
                    "✅ Applied",
                    disabled=True,
                    key=f"role_applied_{live_job_id}",
                    use_container_width=True
                )

            else:

                if st.button(
                    "🚀 Apply Now",
                    type="primary",
                    key=f"role_apply_{live_job_id}",
                    use_container_width=True
                ):

                    st.session_state.selected_application_job = (
                        job
                    )

                    st.session_state.show_application_form = (
                        True
                    )

                    st.rerun()


# ============================================================
# MY PROFILE
# ============================================================

def student_profile_page():

    st.title(
        "👤 My Profile"
    )

    st.caption(
        "Build your professional profile for personalized recommendations."
    )

    profile = st.session_state.get(
        "student_profile",
        {}
    )

    completion = (
        calculate_profile_completion()
    )

    st.progress(
        completion / 100,
        text=(
            f"Profile Completion: "
            f"{completion}%"
        )
    )

    st.divider()

    # ========================================================
    # PERSONAL DETAILS
    # ========================================================

    st.subheader(
        "👤 Personal Details"
    )

    c1, c2 = st.columns(2)

    with c1:

        full_name = st.text_input(
            "Full Name",
            value=profile.get(
                "full_name",
                ""
            ),
            key="profile_full_name"
        )

        email = st.text_input(
            "Email",
            value=profile.get(
                "email",
                ""
            ),
            key="profile_email"
        )

        phone = st.text_input(
            "Phone",
            value=profile.get(
                "phone",
                ""
            ),
            key="profile_phone"
        )

        location = st.text_input(
            "Location",
            value=profile.get(
                "location",
                ""
            ),
            key="profile_location"
        )

    with c2:

        headline = st.text_input(
            "Professional Headline",
            value=profile.get(
                "headline",
                ""
            ),
            key="profile_headline"
        )

        department = st.text_input(
            "Department",
            value=profile.get(
                "department",
                ""
            ),
            key="profile_department"
        )

        degree = st.text_input(
            "Degree",
            value=profile.get(
                "degree",
                "B.Tech"
            ),
            key="profile_degree"
        )

        graduation_year = st.text_input(
            "Graduation Year",
            value=profile.get(
                "graduation_year",
                ""
            ),
            key="profile_graduation_year"
        )

    about = st.text_area(
        "About",
        value=profile.get(
            "about",
            ""
        ),
        height=120,
        key="profile_about"
    )

    st.divider()

    # ========================================================
    # EDUCATION
    # ========================================================

    st.subheader(
        "🎓 Education"
    )

    c1, c2 = st.columns(2)

    with c1:

        college = st.text_input(
            "College / University",
            value=profile.get(
                "college",
                ""
            ),
            key="profile_college"
        )

    with c2:

        cgpa = st.text_input(
            "CGPA / Percentage",
            value=profile.get(
                "cgpa",
                ""
            ),
            key="profile_cgpa"
        )

    st.divider()

    # ========================================================
    # SKILLS
    # ========================================================

    st.subheader(
        "🛠️ Skills"
    )

    existing_skills = profile.get(
        "skills",
        []
    )

    skills_text = st.text_input(
        "Skills",
        value=", ".join(
            str(x)
            for x in existing_skills
        ),
        placeholder=(
            "Python, SQL, Machine Learning, Pandas, Power BI"
        ),
        key="profile_skills"
    )

    skills = [

        item.strip()

        for item in skills_text.split(",")

        if item.strip()

    ]

    if skills:

        cols = st.columns(
            min(
                len(skills),
                4
            )
        )

        for index, skill in enumerate(
            skills
        ):

            with cols[
                index % len(cols)
            ]:

                st.info(
                    f"✓ {skill}"
                )

    st.divider()

    # ========================================================
    # PROJECTS
    # ========================================================

    st.subheader(
        "📂 Projects"
    )

    projects = list(
        profile.get(
            "projects",
            []
        )
    )

    p1, p2 = st.columns(2)

    with p1:

        project_title = st.text_input(
            "Project Title",
            key="new_project_title"
        )

    with p2:

        project_tech = st.text_input(
            "Technologies",
            key="new_project_tech"
        )

    project_description = st.text_area(
        "Project Description",
        key="new_project_description"
    )

    if st.button(
        "➕ Add Project",
        key="add_project_button"
    ):

        if project_title.strip():

            projects.append(
                {
                    "title":
                        project_title.strip(),

                    "description":
                        project_description.strip(),

                    "technologies":
                        project_tech.strip()
                }
            )

            profile["projects"] = (
                projects
            )

            st.session_state.student_profile = (
                profile
            )

            st.rerun()

        else:

            st.warning(
                "Enter a project title."
            )

    for index, project in enumerate(
        projects
    ):

        with st.container(
            border=True
        ):

            st.markdown(
                f"**{project.get('title', 'Project')}**"
            )

            st.write(
                project.get(
                    "description",
                    ""
                )
            )

            st.caption(
                "Technologies: "
                f"{project.get('technologies', '-')}"
            )

            if st.button(
                "🗑️ Remove",
                key=f"remove_project_{index}"
            ):

                projects.pop(index)

                profile["projects"] = (
                    projects
                )

                st.session_state.student_profile = (
                    profile
                )

                st.rerun()

    st.divider()

    # ========================================================
    # CERTIFICATIONS
    # ========================================================

    st.subheader(
        "🏆 Certifications"
    )

    certifications = list(
        profile.get(
            "certifications",
            []
        )
    )

    cert_name = st.text_input(
        "Certification Name",
        key="new_cert_name"
    )

    cert_issuer = st.text_input(
        "Issuing Organization",
        key="new_cert_issuer"
    )

    cert_year = st.text_input(
        "Year",
        key="new_cert_year"
    )

    if st.button(
        "➕ Add Certification",
        key="add_cert_button"
    ):

        if cert_name.strip():

            certifications.append(
                {
                    "name":
                        cert_name.strip(),

                    "issuer":
                        cert_issuer.strip(),

                    "year":
                        cert_year.strip()
                }
            )

            profile[
                "certifications"
            ] = certifications

            st.session_state.student_profile = (
                profile
            )

            st.rerun()

    for index, cert in enumerate(
        certifications
    ):

        with st.container(
            border=True
        ):

            st.markdown(
                f"**{cert.get('name', 'Certification')}**"
            )

            st.write(
                f"Issuer: "
                f"{cert.get('issuer', '-')}"
            )

            st.write(
                f"Year: "
                f"{cert.get('year', '-')}"
            )

            if st.button(
                "🗑️ Remove",
                key=f"remove_cert_{index}"
            ):

                certifications.pop(index)

                profile[
                    "certifications"
                ] = certifications

                st.session_state.student_profile = (
                    profile
                )

                st.rerun()

    st.divider()

    # ========================================================
    # EXPERIENCE
    # ========================================================

    st.subheader(
        "💼 Experience"
    )

    experience = list(
        profile.get(
            "experience",
            []
        )
    )

    experience_title = st.text_input(
        "Job / Internship Title",
        key="new_exp_title"
    )

    experience_company = st.text_input(
        "Company",
        key="new_exp_company"
    )

    experience_duration = st.text_input(
        "Duration",
        key="new_exp_duration"
    )

    experience_description = st.text_area(
        "Description",
        key="new_exp_description"
    )

    if st.button(
        "➕ Add Experience",
        key="add_experience_button"
    ):

        if experience_title.strip():

            experience.append(
                {
                    "title":
                        experience_title.strip(),

                    "company":
                        experience_company.strip(),

                    "duration":
                        experience_duration.strip(),

                    "description":
                        experience_description.strip()
                }
            )

            profile[
                "experience"
            ] = experience

            st.session_state.student_profile = (
                profile
            )

            st.rerun()

        else:

            st.warning(
                "Enter the job or internship title."
            )

    for index, exp in enumerate(
        experience
    ):

        with st.container(
            border=True
        ):

            st.markdown(
                f"**{exp.get('title', 'Experience')}**"
            )

            st.write(
                f"Company: "
                f"{exp.get('company', '-')}"
            )

            st.write(
                f"Duration: "
                f"{exp.get('duration', '-')}"
            )

            st.write(
                exp.get(
                    "description",
                    ""
                )
            )

            if st.button(
                "🗑️ Remove",
                key=f"remove_exp_{index}"
            ):

                experience.pop(index)

                profile[
                    "experience"
                ] = experience

                st.session_state.student_profile = (
                    profile
                )

                st.rerun()

    st.divider()

    # ========================================================
    # SAVE PROFILE TO FASTAPI
    # ========================================================

    if st.button(
        "💾 Save Profile",
        type="primary",
        use_container_width=True,
        key="save_profile_button"
    ):

        updated_profile = {

            "student_id":
                profile.get(
                    "student_id",
                    get_logged_in_student().get(
                        "student_id",
                        ""
                    )
                ),

            "full_name":
                full_name,

            "email":
                email,

            "phone":
                phone,

            "location":
                location,

            "headline":
                headline,

            "about":
                about,

            "department":
                department,

            "degree":
                degree,

            "graduation_year":
                graduation_year,

            "college":
                college,

            "cgpa":
                cgpa,

            "skills":
                skills,

            "projects":
                projects,

            "certifications":
                certifications,

            "experience":
                experience,

        }

        success, message = (
            save_student_profile_to_api(
                updated_profile
            )
        )

        if success:

            st.success(
                "✅ Profile saved successfully to PostgreSQL."
            )

            st.session_state.profile_loaded = (
                True
            )

            st.rerun()

        else:

            st.error(
                f"❌ {message}"
            )


# ============================================================
# RESUME & DOCUMENTS
# ============================================================

def documents_page():

    st.title(
        "📄 Resume & Documents"
    )

    st.caption(
        "Manage your resume and supporting documents."
    )

    # ========================================================
    # RESUME
    # ========================================================

    st.subheader(
        "📄 Resume"
    )

    resume = st.file_uploader(
        "Upload Resume",
        type=[
            "pdf",
            "doc",
            "docx"
        ],
        key="resume_upload"
    )

    if resume:

        st.session_state.student_resume = {

            "name":
                resume.name,

            "type":
                resume.type,

            "size":
                resume.size,

            "data":
                resume.getvalue()

        }

        st.success(
            f"✅ Resume uploaded: {resume.name}"
        )

    elif st.session_state.get(
        "student_resume"
    ):

        saved = (
            st.session_state.student_resume
        )

        st.info(
            f"Current Resume: "
            f"**{saved.get('name', 'Resume')}**"
        )

        try:

            size = (
                saved.get(
                    "size",
                    0
                )
            )

            st.write(
                f"Size: {size / 1024:.1f} KB"
            )

        except Exception:

            pass

    else:

        st.info(
            "No resume uploaded yet."
        )

    st.divider()

    # ========================================================
    # SUPPORTING DOCUMENTS
    # ========================================================

    st.subheader(
        "📁 Supporting Documents"
    )

    documents = st.file_uploader(
        "Upload Documents",
        type=[
            "pdf",
            "doc",
            "docx",
            "png",
            "jpg",
            "jpeg"
        ],
        accept_multiple_files=True,
        key="supporting_documents_upload"
    )

    if documents:

        st.session_state.student_documents = [

            {

                "name":
                    document.name,

                "type":
                    document.type,

                "size":
                    document.size,

                "data":
                    document.getvalue()

            }

            for document in documents

        ]

        st.success(
            f"✅ {len(documents)} document(s) uploaded."
        )

    saved_documents = (
        st.session_state.get(
            "student_documents",
            []
        )
    )

    if saved_documents:

        st.write(
            "### Uploaded Documents"
        )

        for document in saved_documents:

            with st.container(
                border=True
            ):

                st.write(
                    f"📄 **{document.get('name', 'Document')}**"
                )

                st.caption(
                    f"{document.get('type', '-')}"
                    f" • "
                    f"{document.get('size', 0) / 1024:.1f} KB"
                )

    else:

        st.info(
            "No supporting documents uploaded yet."
        )

    st.warning(
        "🔐 Prototype: use dummy/non-sensitive documents only. "
        "Do not upload Aadhaar, PAN, bank details, passwords, "
        "or other highly sensitive identity documents."
    )


# ============================================================
# STUDENT SIDEBAR + ROUTING
# ============================================================

def student_dashboard():

    student = get_logged_in_student()

    if not student:

        st.session_state.student_logged_in = (
            False
        )

        return

    # ========================================================
    # SIDEBAR
    # ========================================================

    st.sidebar.divider()

    st.sidebar.markdown(
        f"### 👤 "
        f"{student.get('student_name', 'Student')}"
    )

    st.sidebar.caption(
        f"{student.get('department', '-')}"
        f" • Student"
    )

    pages = [

        "Dashboard",


        "Recommended Jobs",

        "Role Intelligence",

        "Future Hiring",

        "Saved Jobs",

        "Notifications",

        "My Applications",

        "My Profile",

     

    ]

    # --------------------------------------------------------
    # Keep selected page valid
    # --------------------------------------------------------

    current_page = st.session_state.get(
    "student_page",
    "Dashboard"
    )

    if current_page not in pages:
        current_page = "Dashboard"

    selected_page = st.sidebar.radio(
    "Student Portal",
    pages,
    index=pages.index(current_page),
    key="student_page_radio"
)

    st.session_state.student_page = selected_page

    # ========================================================
    # LOGOUT
    # ========================================================

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True,
        key="student_logout"
    ):

        api_client = (
            st.session_state.get(
                "api_client"
            )
        )

        if api_client:

            api_client.clear_token()

        st.session_state.access_token = None

        st.session_state.student_logged_in = (
            False
        )

        st.session_state.logged_in_student = (
            None
        )

        st.session_state.student_profile = (
            {}
        )

        st.session_state.profile_loaded = (
            False
        )

        st.session_state.show_application_form = (
            False
        )

        st.session_state.selected_application_job = (
            None
        )

        st.session_state.student_page = (
            "Dashboard"
        )

        st.rerun()

    # ========================================================
    # APPLICATION FORM
    # ========================================================

    if st.session_state.get(
        "show_application_form",
        False
    ):

        application_form_page()

        return

    # ========================================================
    # ROUTING
    # ========================================================

    if selected_page == "Dashboard":

        dashboard_page()

    elif selected_page == "Find Jobs":

        find_jobs_page()

    elif selected_page == "Recommended Jobs":

        show_recommended_jobs()

 

    elif selected_page == "Role Intelligence":

         show_role_intelligence()

    elif selected_page == "Future Hiring":

        future_hiring_page()

    elif selected_page == "Saved Jobs":

        saved_jobs_page()

    elif selected_page == "Notifications":

        notifications_page()

    elif selected_page == "My Applications":

        application_tracking_page()

    elif selected_page == "My Profile":

        student_profile_page()

    elif selected_page == "Resume & Documents":

        documents_page()


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def show_student_home():

    initialize_notification_state()

    initialize_student_state()

    # ========================================================
    # AUTHENTICATION FIRST
    # ========================================================

    if not st.session_state.get(
        "student_logged_in",
        False
    ):

        student_login()

        return

    # ========================================================
    # MAKE SURE TOKEN IS LOADED
    # ========================================================

    api_client = get_api_client()

    if not st.session_state.get(
        "access_token"
    ):

        st.session_state.student_logged_in = (
            False
        )

        student_login()

        return

    # ========================================================
    # LOAD PROFILE ONCE PER SESSION
    # ========================================================

    if not st.session_state.get(
        "profile_loaded",
        False
    ):

        load_student_profile_from_api()

    # ========================================================
    # STUDENT PORTAL
    # ========================================================

    student_dashboard()