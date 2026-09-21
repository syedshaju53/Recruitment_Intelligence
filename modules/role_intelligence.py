# ============================================================
# ROLE INTELLIGENCE
# AI-Powered Recruitment Intelligence Portal
# ============================================================

import os
import re

import pandas as pd
import streamlit as st

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from api.client import APIClient


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_database_engine():
    """
    Create PostgreSQL SQLAlchemy engine safely.

    URL.create() is used so special characters in the password
    such as @, :, /, #, ?, % do not break the connection URL.
    """

    password = os.getenv("POSTGRES_PASSWORD")

    if not password:
        raise ValueError(
            "POSTGRES_PASSWORD is not configured."
        )

    db_url = URL.create(
        drivername="postgresql+psycopg2",
        username="postgres",
        password=password,
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=5432,
        database="recruitment_db",
    )

    return create_engine(
        db_url,
        pool_pre_ping=True,
    )


# ============================================================
# BRANCH KEYWORDS
# ============================================================

BRANCH_KEYWORDS = {

    "CSE": [
        "software",
        "software engineer",
        "software developer",
        "application developer",
        "web developer",
        "frontend",
        "front end",
        "backend",
        "back end",
        "full stack",
        "fullstack",
        "python",
        "java",
        "javascript",
        "typescript",
        "react",
        "angular",
        "node",
        "nodejs",
        "django",
        "flask",
        "fastapi",
        "machine learning",
        "machine-learning",
        "artificial intelligence",
        "ai engineer",
        "ml engineer",
        "data scientist",
        "data science",
        "data analyst",
        "data analytics",
        "deep learning",
        "nlp",
        "natural language processing",
        "computer vision",
        "devops",
        "cloud engineer",
        "cloud computing",
        "aws",
        "azure",
        "gcp",
        "cyber security",
        "cybersecurity",
        "information security",
        "network engineer",
        "database",
        "sql",
        "postgresql",
        "mysql",
        "mongodb",
        "qa engineer",
        "test engineer",
        "automation tester",
        "automation engineer",
        "embedded software",
        "programmer",
        "developer",
        "technical support",
        "technology",
        "it",
    ],

    "ECE": [
        "electronics",
        "electronics engineer",
        "electronic engineer",
        "embedded",
        "embedded engineer",
        "embedded systems",
        "embedded software",
        "firmware",
        "vlsi",
        "asic",
        "fpga",
        "microcontroller",
        "microprocessor",
        "iot",
        "internet of things",
        "robotics",
        "automation",
        "instrumentation",
        "communication engineer",
        "telecommunication",
        "telecommunications",
        "rf engineer",
        "radio frequency",
        "signal processing",
        "digital signal",
        "analog",
        "pcb",
        "circuit design",
        "hardware engineer",
        "hardware design",
        "semiconductor",
        "verification engineer",
        "validation engineer",
        "electrical and electronics",
    ],

    "EEE": [
        "electrical engineer",
        "electrical engineering",
        "electrical",
        "power systems",
        "power system",
        "power electronics",
        "power engineer",
        "electrical design",
        "electrical maintenance",
        "electrical project",
        "substation",
        "transformer",
        "switchgear",
        "motor",
        "generator",
        "renewable energy",
        "solar",
        "wind energy",
        "energy systems",
        "control systems",
        "industrial automation",
        "plc",
        "scada",
        "instrumentation",
        "electronics",
        "embedded",
        "automation engineer",
    ],

    "Mechanical": [
        "mechanical engineer",
        "mechanical engineering",
        "mechanical",
        "manufacturing",
        "manufacturing engineer",
        "production engineer",
        "production",
        "automotive",
        "automobile",
        "automotive engineer",
        "cad",
        "cam",
        "cae",
        "solidworks",
        "autocad",
        "catia",
        "creo",
        "ansys",
        "nx cad",
        "design engineer",
        "mechanical design",
        "product design",
        "product development",
        "industrial engineering",
        "industrial engineer",
        "quality engineer",
        "quality control",
        "quality assurance",
        "maintenance engineer",
        "maintenance",
        "thermal",
        "thermodynamics",
        "hvac",
        "piping",
        "process engineer",
        "process engineering",
        "tool design",
        "machining",
        "cnc",
        "automotive design",
        "mechatronics",
        "robotics",
    ],

    "Civil": [
        "civil engineer",
        "civil engineering",
        "civil",
        "construction",
        "construction engineer",
        "site engineer",
        "site supervisor",
        "structural engineer",
        "structural engineering",
        "structure",
        "structural design",
        "architecture",
        "architectural",
        "building design",
        "quantity surveyor",
        "quantity surveying",
        "estimation engineer",
        "planning engineer",
        "project engineer",
        "project management",
        "infrastructure",
        "road construction",
        "highway",
        "bridge",
        "building construction",
        "concrete",
        "steel structure",
        "autocad civil",
        "civil 3d",
        "revit",
        "staad",
        "staad pro",
        "primavera",
        "surveying",
        "land surveying",
        "geotechnical",
        "geotechnical engineer",
        "environmental engineer",
        "water resources",
    ],
}


# ============================================================
# ACADEMIC / NON-JOB KEYWORDS
# ============================================================

ACADEMIC_KEYWORDS = [
    "professor",
    "assistant professor",
    "associate professor",
    "lecturer",
    "faculty",
    "teaching",
    "teacher",
    "school teacher",
    "trainer",
    "academic coordinator",
    "research scholar",
    "research assistant",
    "phd",
    "doctoral",
    "post doctoral",
    "postdoctoral",
    "principal",
    "dean",
    "college faculty",
    "university faculty",
]


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(value):
    """
    Convert any value into normalized searchable text.
    """

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    value = str(value)

    value = value.lower()

    value = re.sub(
        r"[^a-z0-9+#.&/\- ]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


# ============================================================
# ACADEMIC JOB CHECK
# ============================================================

def is_academic_job(job_text):
    """
    Remove academic/teaching roles from the live-job results.
    """

    text_value = clean_text(job_text)

    for keyword in ACADEMIC_KEYWORDS:

        if keyword in text_value:
            return True

    return False


# ============================================================
# BRANCH MATCHING
# ============================================================

def matches_branch(job, branch):
    """
    Determine whether a live opening is relevant to the
    selected academic branch.

    Matching is performed against:
    - job title
    - department
    - skills
    - job description
    - experience
    """

    if branch not in BRANCH_KEYWORDS:
        return False

    searchable_parts = [
        job.get("job_title", ""),
        job.get("department", ""),
        job.get("skills", ""),
        job.get("job_description", ""),
        job.get("experience", ""),
    ]

    searchable_text = clean_text(
        " ".join(
            str(part)
            for part in searchable_parts
            if part is not None
        )
    )

    if not searchable_text:
        return False

    # --------------------------------------------------------
    # Academic job exclusion
    # --------------------------------------------------------

    if is_academic_job(searchable_text):
        return False

    # --------------------------------------------------------
    # Branch keyword matching
    # --------------------------------------------------------

    keywords = BRANCH_KEYWORDS[branch]

    for keyword in keywords:

        keyword_clean = clean_text(keyword)

        if not keyword_clean:
            continue

        if keyword_clean in searchable_text:
            return True

    return False


# ============================================================
# LOAD LIVE JOBS
# ============================================================

def load_live_jobs():
    """
    Load currently open live jobs from PostgreSQL.
    """

    try:

        engine = get_database_engine()

        query = text(
            """
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
                job_description,
                posted_date,
                updated_date,
                application_url,
                source,
                status,
                last_checked
            FROM live_jobs
            WHERE status = 'open'
            ORDER BY posted_date DESC NULLS LAST
            """
        )

        with engine.connect() as connection:

            df = pd.read_sql(
                query,
                connection,
            )

        engine.dispose()

        if df.empty:
            return df

        # ----------------------------------------------------
        # Clean text columns
        # ----------------------------------------------------

        text_columns = [
            "company_name",
            "job_title",
            "department",
            "skills",
            "experience",
            "salary",
            "location",
            "work_mode",
            "job_description",
            "application_url",
            "source",
        ]

        for column in text_columns:

            if column in df.columns:

                df[column] = (
                    df[column]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )

        # ----------------------------------------------------
        # Convert posted date
        # ----------------------------------------------------

        if "posted_date" in df.columns:

            df["posted_date"] = pd.to_datetime(
                df["posted_date"],
                errors="coerce",
            )

        # ----------------------------------------------------
        # Remove academic jobs
        # ----------------------------------------------------

        if not df.empty:

            searchable = (
                df["job_title"].fillna("").astype(str)
                + " "
                + df["department"].fillna("").astype(str)
                + " "
                + df["skills"].fillna("").astype(str)
                + " "
                + df["job_description"].fillna("").astype(str)
            )

            df = df[
                ~searchable.apply(is_academic_job)
            ].copy()

        return df

    except Exception as e:

        st.error(
            f"Unable to load live openings: {e}"
        )

        return pd.DataFrame()


# ============================================================
# FORMAT DATE
# ============================================================

def format_posted_date(value):

    if value is None:
        return "Date unavailable"

    try:

        date_value = pd.to_datetime(
            value,
            errors="coerce",
        )

        if pd.isna(date_value):
            return "Date unavailable"

        return date_value.strftime(
            "%d %b %Y"
        )

    except Exception:

        return "Date unavailable"


# ============================================================
# FORMAT MONTH
# ============================================================

def get_posted_month(value):

    try:

        date_value = pd.to_datetime(
            value,
            errors="coerce",
        )

        if pd.isna(date_value):
            return ""

        return date_value.strftime(
            "%B %Y"
        )

    except Exception:

        return ""


# ============================================================
# DISPLAY JOB
# ============================================================

def display_role_job(job, index):
    """
    Display one live role.
    """

    live_job_id = job.get("id")

    if live_job_id is None:
        return

    try:
        live_job_id = int(
            float(live_job_id)
        )
    except (
        ValueError,
        TypeError,
    ):
        return

    company = (
        str(
            job.get(
                "company_name",
                "Company",
            )
        ).strip()
        or "Company"
    )

    title = (
        str(
            job.get(
                "job_title",
                "Job Role",
            )
        ).strip()
        or "Job Role"
    )

    location = (
        str(
            job.get(
                "location",
                "Location not specified",
            )
        ).strip()
        or "Location not specified"
    )

    work_mode = (
        str(
            job.get(
                "work_mode",
                "Not specified",
            )
        ).strip()
        or "Not specified"
    )

    salary = (
        str(
            job.get(
                "salary",
                "Not disclosed",
            )
        ).strip()
        or "Not disclosed"
    )

    skills = (
        str(
            job.get(
                "skills",
                "",
            )
        ).strip()
    )

    experience = (
        str(
            job.get(
                "experience",
                "Not specified",
            )
        ).strip()
        or "Not specified"
    )

    source = (
        str(
            job.get(
                "source",
                "Live Source",
            )
        ).strip()
        or "Live Source"
    )

    posted_date = format_posted_date(
        job.get("posted_date")
    )

    application_url = (
        str(
            job.get(
                "application_url",
                "",
            )
        ).strip()
    )

    # ========================================================
    # JOB CARD
    # ========================================================

    st.markdown(
        f"""
        <div style="
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 14px;
            padding: 20px;
            margin-top: 14px;
            margin-bottom: 14px;
            background: rgba(255,255,255,0.025);
        ">

        <div style="
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 5px;
        ">
            💼 {title}
        </div>

        <div style="
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 14px;
        ">
            🏢 {company}
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # JOB INFORMATION
    # ========================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            f"📍 **Location**  \n{location}"
        )

    with col2:

        st.markdown(
            f"🏠 **Work Mode**  \n{work_mode}"
        )

    with col3:

        st.markdown(
            f"📅 **Posted**  \n{posted_date}"
        )

    col4, col5, col6 = st.columns(3)

    with col4:

        st.markdown(
            f"💰 **Salary**  \n{salary}"
        )

    with col5:

        st.markdown(
            f"🎯 **Experience**  \n{experience}"
        )

    with col6:

        st.markdown(
            f"🔗 **Source**  \n{source}"
        )

    # ========================================================
    # SKILLS
    # ========================================================

    if skills:

        st.markdown(
            f"🛠️ **Skills:** {skills}"
        )

    # ========================================================
    # JOB DESCRIPTION
    # ========================================================

    description = str(
        job.get(
            "job_description",
            "",
        )
    ).strip()

    if description:

        with st.expander(
            "📄 View Job Description"
        ):

            st.write(description)

    # ========================================================
    # SAVE + APPLY
    # ========================================================

    save_col, apply_col = st.columns(2)

    # --------------------------------------------------------
    # SAVE JOB
    # --------------------------------------------------------

    with save_col:

        save_key = (
            f"role_save_job_{live_job_id}_{index}"
        )

        if st.button(
            "🔖 Save Job",
            key=save_key,
            width="stretch",
        ):

            try:

                api_client = APIClient()

                access_token = st.session_state.get("access_token")

                if not access_token:
                    st.error("❌ Session expired. Please login again.")
                    st.stop()

                api_client.set_token(access_token)

                response = (
                    api_client.save_job(
                        live_job_id=live_job_id
                    )
                )

                if response.status_code in (
                    200,
                    201,
                ):

                    st.success(
                        "✅ Job saved successfully!"
                    )

                elif response.status_code == 400:

                    try:

                        message = (
                            response.json()
                            .get(
                                "detail",
                                "Job already saved.",
                            )
                        )

                    except Exception:

                        message = (
                            "Job already saved."
                        )

                    st.warning(
                        f"⚠️ {message}"
                    )

                else:

                    st.error(
                        f"❌ Save failed | Status: {response.status_code}"
                    )

                    try:
                        st.code(response.text)
                    except Exception:
                        pass

            except Exception as e:

                st.error(
                    f"❌ Save failed: {e}"
                )

    # --------------------------------------------------------
    # APPLY NOW
    # --------------------------------------------------------

    with apply_col:

        apply_key = (
            f"role_apply_job_{live_job_id}_{index}"
        )

        if st.button(
            "🚀 Apply Now",
            key=apply_key,
            type="primary",
            width="stretch",
        ):

            # Convert Series to dictionary
            job_dict = job.to_dict()

            # Explicit live job ID
            job_dict[
                "live_job_id"
            ] = live_job_id

            # Store selected job for the
            # existing application form
            st.session_state[
                "selected_application_job"
            ] = job_dict

            st.session_state[
                "show_application_form"
            ] = True

            st.rerun()

    # ========================================================
    # OFFICIAL APPLICATION URL
    # ========================================================

    # This is shown only as source information.
    # Application itself remains inside the platform.
    if application_url:

        st.caption(
            "ℹ️ Application is handled through the "
            "Recruitment Intelligence platform."
        )

    st.divider()


# ============================================================
# ROLE INTELLIGENCE PAGE
# ============================================================

def role_intelligence_page():

    # ========================================================
    # HEADER
    # ========================================================

    st.title(
        "💼 Role Intelligence"
    )

    st.caption(
        "Explore live job openings by academic branch "
        "and posting month."
    )

    # ========================================================
    # LOAD LIVE JOBS
    # ========================================================

    live_jobs = load_live_jobs()

    if live_jobs.empty:

        st.warning(
            "No live openings are currently available."
        )

        return

    # ========================================================
    # ONLY OPEN JOBS
    # ========================================================

    if "status" in live_jobs.columns:

        live_jobs = live_jobs[
            live_jobs["status"]
            .astype(str)
            .str.lower()
            .eq("open")
        ].copy()

    if live_jobs.empty:

        st.warning(
            "No live openings are currently available."
        )

        return

    # ========================================================
    # BUILD MONTH COLUMN
    # ========================================================

    live_jobs[
        "posted_month"
    ] = live_jobs[
        "posted_date"
    ].apply(
        get_posted_month
    )

    # ========================================================
    # FILTER SECTION
    # ========================================================

    st.markdown(
        "### 🔎 Find Roles"
    )

    filter_col1, filter_col2 = st.columns(
        2
    )

    # ========================================================
    # BRANCH DROPDOWN
    # ========================================================

    with filter_col1:

        st.markdown(
            "##### 📚 Select Department"
        )

        branch_options = [
            "CSE",
            "ECE",
            "EEE",
            "Mechanical",
            "Civil",
        ]

        selected_branch = st.selectbox(
            "Select Department",
            branch_options,
            key="role_intelligence_department",
            label_visibility="collapsed",
        )

    # ========================================================
    # MONTH DROPDOWN
    # ========================================================

    with filter_col2:

        st.markdown(
            "##### 📅 Select Month"
        )

        available_months = (
            live_jobs[
                live_jobs["posted_month"] != ""
            ]["posted_month"]
            .dropna()
            .unique()
            .tolist()
        )

        # Convert month strings into actual dates
        # so they appear newest first.
        month_dates = []

        for month in available_months:

            try:

                month_date = pd.to_datetime(
                    month,
                    format="%B %Y",
                    errors="coerce",
                )

                if not pd.isna(month_date):

                    month_dates.append(
                        (
                            month_date,
                            month,
                        )
                    )

            except Exception:

                pass

        month_dates.sort(
            key=lambda x: x[0],
            reverse=True,
        )

        sorted_months = [
            item[1]
            for item in month_dates
        ]

        if not sorted_months:

            st.info(
                "No posting month information "
                "is available for the current live openings."
            )

            return

        selected_month = st.selectbox(
            "Select Month",
            sorted_months,
            key="role_intelligence_month",
            label_visibility="collapsed",
        )

    st.divider()

    # ========================================================
    # BRANCH FILTER
    # ========================================================

    branch_filtered_jobs = []

    for _, job in live_jobs.iterrows():

        job_dict = job.to_dict()

        if matches_branch(
            job_dict,
            selected_branch,
        ):

            branch_filtered_jobs.append(
                job
            )

    if branch_filtered_jobs:

        branch_filtered_jobs = pd.DataFrame(
            branch_filtered_jobs
        )

    else:

        branch_filtered_jobs = pd.DataFrame(
            columns=live_jobs.columns
        )

    # ========================================================
    # MONTH FILTER
    # ========================================================

    if not branch_filtered_jobs.empty:

        branch_filtered_jobs = (
            branch_filtered_jobs[
                branch_filtered_jobs[
                    "posted_month"
                ].eq(selected_month)
            ]
            .copy()
        )

    # ========================================================
    # SORT NEWEST FIRST
    # ========================================================

    if not branch_filtered_jobs.empty:

        branch_filtered_jobs = (
            branch_filtered_jobs.sort_values(
                by="posted_date",
                ascending=False,
                na_position="last",
            )
        )

    # ========================================================
    # RESULTS HEADER
    # ========================================================

    st.markdown(
        "### 📊 Role Results"
    )

    metric_col1, metric_col2, metric_col3 = (
        st.columns(3)
    )

    with metric_col1:

        st.metric(
            "💼 Roles",
            len(branch_filtered_jobs),
        )

    with metric_col2:

        st.metric(
            "🎓 Department",
            selected_branch,
        )

    with metric_col3:

        st.metric(
            "📅 Month",
            selected_month,
        )

    # ========================================================
    # NO RESULTS
    # ========================================================

    if branch_filtered_jobs.empty:

        st.info(
            f"No live {selected_branch} openings "
            f"were found for {selected_month}."
        )

        st.caption(
            "Try another month to explore available "
            "live openings."
        )

        return

    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    st.success(
        f"Found {len(branch_filtered_jobs)} "
        f"live opening(s) for {selected_branch} "
        f"in {selected_month}."
    )

    for index, (_, job) in enumerate(
        branch_filtered_jobs.iterrows()
    ):

        display_role_job(
            job,
            index,
        )


# ============================================================
# PUBLIC ENTRY POINT
# ============================================================

def show_role_intelligence():

    role_intelligence_page()