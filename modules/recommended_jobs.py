# ============================================================
# AI JOB RECOMMENDATION ENGINE
# 97K DATASET + LIVE COMPANY JOBS
# ============================================================

import os
import re
import pandas as pd
import streamlit as st
from api.client import APIClient

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()





# ============================================================
# API CLIENT
# ============================================================

def get_api_client():

    api_client = st.session_state.get(
        "api_client"
    )

    if api_client is None:

        api_client = APIClient()

        st.session_state.api_client = (
            api_client
        )

    token = st.session_state.get(
        "access_token"
    )

    if token:

        api_client.set_token(
            token
        )

    return api_client


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATASET_FILE = os.path.join(
    BASE_DIR,
    "data",
    "indian-job-market-dataset-2025.xlsx"
)

import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine

DB_USER = "postgres"
DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = "5432"
DB_NAME = "recruitment_db"

DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD")

if not DB_PASSWORD:
    raise RuntimeError("POSTGRES_PASSWORD is not set.")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# ============================================================
# BRANCH KEYWORDS
# ============================================================

BRANCH_KEYWORDS = {

    "cse": [
        "software engineer",
        "software developer",
        "data analyst",
        "data scientist",
        "data engineer",
        "machine learning",
        "ml engineer",
        "ai engineer",
        "artificial intelligence",
        "python developer",
        "java developer",
        "full stack",
        "backend",
        "frontend",
        "cloud engineer",
        "devops",
        "cyber security",
        "cybersecurity",
        "database",
        "sql",
        "qa engineer",
        "automation engineer",
        "network engineer",
        "web developer",
        "application developer",
        "programmer",
        "software",
        "data science",
        "deep learning",
        "generative ai",
        "genai",
        "llm",
        "nlp"
    ],

    "ece": [
        "electronics engineer",
        "embedded engineer",
        "embedded systems",
        "firmware engineer",
        "vlsi",
        "asic",
        "fpga",
        "hardware engineer",
        "iot engineer",
        "iot",
        "semiconductor",
        "pcb",
        "telecom engineer",
        "communication engineer",
        "electrical electronics",
        "electronics"
    ],

    "civil": [
        "civil engineer",
        "structural engineer",
        "site engineer",
        "construction engineer",
        "planning engineer",
        "quantity surveyor",
        "bim engineer",
        "autocad",
        "project engineer",
        "civil design",
        "construction",
        "structural design"
    ],

    "mechanical": [
        "mechanical engineer",
        "mechanical design",
        "cad engineer",
        "manufacturing engineer",
        "production engineer",
        "automotive engineer",
        "maintenance engineer",
        "quality engineer",
        "hvac engineer",
        "process engineer",
        "industrial engineer",
        "design engineer",
        "manufacturing",
        "automotive"
    ]
}


# ============================================================
# ACADEMIC / NON-COMPANY EXCLUSION
# ============================================================

ACADEMIC_KEYWORDS = [
    "professor",
    "assistant professor",
    "associate professor",
    "lecturer",
    "teacher",
    "faculty",
    "teaching",
    "tutor",
    "academic",
    "education",
    "school",
    "college",
    "university",
    "principal",
    "dean"
]




# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(value):

    if value is None:
        return ""

    # Handle lists / tuples / sets
    if isinstance(
        value,
        (list, tuple, set)
    ):
        value = " ".join(
            str(x)
            for x in value
            if x is not None
        )

    # Handle pandas Series / NumPy arrays
    elif hasattr(
        value,
        "tolist"
    ) and not isinstance(
        value,
        (str, bytes)
    ):
        try:
            converted = value.tolist()

            if isinstance(
                converted,
                list
            ):
                value = " ".join(
                    str(x)
                    for x in converted
                    if x is not None
                )
            else:
                value = converted

        except Exception:
            value = str(value)

    # Handle scalar NaN
    try:

        if pd.isna(value):
            return ""

    except (
        ValueError,
        TypeError
    ):
        pass

    value = str(value)

    value = re.sub(
        r"<[^>]+>",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip().lower()


# ============================================================
# CHECK ACADEMIC JOB
# ============================================================

def is_academic_job(text_value):

    text_value = clean_text(
        text_value
    )

    for keyword in ACADEMIC_KEYWORDS:

        if keyword in text_value:
            return True

    return False


# ============================================================
# CHECK BRANCH
# ============================================================

def matches_branch(
    text_value,
    branch
):

    text_value = clean_text(
        text_value
    )

    keywords = BRANCH_KEYWORDS.get(
        branch.lower(),
        []
    )

    return any(
        keyword in text_value
        for keyword in keywords
    )


# ============================================================
# LOAD 97K DATASET
# ============================================================

@st.cache_data
def load_reference_jobs():

    if not os.path.exists(
        DATASET_FILE
    ):
        st.error(
            f"97K dataset not found:\n\n"
            f"{DATASET_FILE}"
        )

        return pd.DataFrame()

    df = pd.read_excel(
        DATASET_FILE
    )

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(
            " ",
            "_",
            regex=False
        )
    )

    # --------------------------------------------------------
    # Rename columns
    # --------------------------------------------------------

    rename_map = {

        "jobid": "job_id",

        "companyname":
            "company_name",

        "tagsandskills":
            "skills",

        "jobdescription":
            "job_description",

        "minimumsalary":
            "minimum_salary",

        "maximumsalary":
            "maximum_salary",

        "minimumexperience":
            "minimum_experience",

        "maximumexperience":
            "maximum_experience"
    }

    df = df.rename(
        columns=rename_map
    )

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required = [

        "job_id",
        "title",
        "company_name",
        "skills",
        "experience",
        "location",
        "job_description"
    ]

    for column in required:

        if column not in df.columns:
            df[column] = ""

    # --------------------------------------------------------
    # Clean columns
    # --------------------------------------------------------

    for column in required:

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # --------------------------------------------------------
    # Create searchable text
    # --------------------------------------------------------

    df["recommendation_text"] = (

        df["title"].map(clean_text)
        + " "
        + df["company_name"].map(clean_text)
        + " "
        + df["skills"].map(clean_text)
        + " "
        + df["experience"].map(clean_text)
        + " "
        + df["location"].map(clean_text)
        + " "
        + df["job_description"]
        .map(clean_text)
        .str[:2500]
    )

    # --------------------------------------------------------
    # Remove academic jobs
    # --------------------------------------------------------

    df = df[
        ~df["recommendation_text"]
        .apply(is_academic_job)
    ].copy()

    return df


# ============================================================
# LOAD LIVE JOBS FROM POSTGRESQL
# ============================================================

def load_live_jobs():

    try:

        engine = create_engine(
            DATABASE_URL
        )

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
                connection
            )

        engine.dispose()

        if df.empty:
            return df

        # ----------------------------------------------------
        # Clean values
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
            "source"
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
        # Searchable text
        # ----------------------------------------------------

        df["recommendation_text"] = (

            df["job_title"].map(clean_text)
            + " "
            + df["company_name"].map(clean_text)
            + " "
            + df["department"].map(clean_text)
            + " "
            + df["skills"].map(clean_text)
            + " "
            + df["experience"].map(clean_text)
            + " "
            + df["location"].map(clean_text)
            + " "
            + df["work_mode"].map(clean_text)
            + " "
            + df["job_description"]
            .map(clean_text)
            .str[:2500]
        )

        # ----------------------------------------------------
        # Remove academic jobs
        # ----------------------------------------------------

        df = df[
            ~df["recommendation_text"]
            .apply(is_academic_job)
        ].copy()

        return df

    except Exception as e:

        st.error(
            f"Unable to load live jobs:\n\n{e}"
        )

        return pd.DataFrame()


# ============================================================
# BUILD STUDENT PROFILE TEXT
# ============================================================

def build_student_profile(profile):

    if not profile:
        return ""

    values = []

    possible_fields = [

        "department",
        "branch",
        "degree",
        "headline",
        "about",
        "skills",
        "projects",
        "experience",
        "location"
    ]

    for field in possible_fields:

        value = profile.get(
            field,
            ""
        )

        if isinstance(value, list):

            value = " ".join(
                str(x)
                for x in value
            )

        if value:

            values.append(
                str(value)
            )

    return " ".join(
        values
    )


# ============================================================
# GET STUDENT BRANCH
# ============================================================

def get_student_branch(profile):

    if not profile:
        return "cse"

    department = str(
        profile.get(
            "department",
            profile.get(
                "branch",
                "cse"
            )
        )
    ).lower()

    if "ece" in department:
        return "ece"

    if "civil" in department:
        return "civil"

    if "mechanical" in department:
        return "mechanical"

    return "cse"


# ============================================================
# RECOMMEND JOBS
# ============================================================

def recommend_jobs(
    jobs_df,
    student_profile,
    branch,
    top_n=10
):

    if jobs_df.empty:
        return pd.DataFrame()

    # --------------------------------------------------------
    # Branch filtering
    # --------------------------------------------------------

    branch_mask = jobs_df[
        "recommendation_text"
    ].apply(
        lambda x:
        matches_branch(
            x,
            branch
        )
    )

    filtered = jobs_df[
        branch_mask
    ].copy()

    if filtered.empty:

        return pd.DataFrame()

    # --------------------------------------------------------
    # Student profile
    # --------------------------------------------------------

    profile_text = build_student_profile(
        student_profile
    )

    if not profile_text.strip():

        return filtered.head(
            top_n
        )

    # --------------------------------------------------------
    # TF-IDF
    # --------------------------------------------------------

    corpus = (

        filtered[
            "recommendation_text"
        ]
        .fillna("")
        .tolist()
    )

    corpus.append(
        clean_text(
            profile_text
        )
    )

    vectorizer = TfidfVectorizer(

        lowercase=True,

        stop_words="english",

        ngram_range=(1, 2),

        min_df=1,

        max_features=15000,

        sublinear_tf=True
    )

    matrix = vectorizer.fit_transform(
        corpus
    )

    profile_vector = matrix[-1]

    job_vectors = matrix[:-1]

    similarity = cosine_similarity(

        profile_vector,

        job_vectors
    ).flatten()

    filtered[
        "match_score"
    ] = similarity * 100

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    filtered = filtered.sort_values(

        by="match_score",

        ascending=False
    )

    return filtered.head(
        top_n
    ).copy()




# ============================================================
# LIVE JOB AI MATCHING ENGINE
# ============================================================

def normalize_tokens(value):
    """
    Convert text/list values into a normalized set of tokens.
    """

    if value is None:
        return set()

    if isinstance(value, list):
        value = " ".join(
            str(x) for x in value
        )

    value = clean_text(value)

    if not value:
        return set()

    # Handle common separators
    value = re.sub(
        r"[,;/|&]+",
        " ",
        value
    )

    tokens = re.findall(
        r"[a-zA-Z0-9+#.]+",
        value
    )

    return {
        token.strip(".")
        for token in tokens
        if len(token.strip(".")) > 1
    }


def extract_student_skills(profile):
    """
    Extract student skills from profile.
    """

    if not profile:
        return set()

    skills = profile.get(
        "skills",
        ""
    )

    return normalize_tokens(
        skills
    )


def extract_job_skills(job):
    """
    Extract skills from a live job.
    """

    skills = job.get(
        "skills",
        ""
    )

    return normalize_tokens(
        skills
    )


def calculate_skills_match(
    student_skills,
    job_skills
):
    """
    Skills Match = percentage of student
    skills found in the job requirement.
    """

    if not student_skills:
        return 0.0

    if not job_skills:
        return 0.0

    matched = (
        student_skills
        & job_skills
    )

    return (
        len(matched)
        / len(student_skills)
    ) * 100


def calculate_role_match(
    profile,
    job
):
    """
    Role Match based on student's profile text
    and live job title.
    """

    profile_text = clean_text(
        build_student_profile(profile)
    )

    job_title = clean_text(
        job.get(
            "job_title",
            ""
        )
    )

    if not profile_text or not job_title:
        return 0.0

    profile_tokens = normalize_tokens(
        profile_text
    )

    title_tokens = normalize_tokens(
        job_title
    )

    if not title_tokens:
        return 0.0

    common = (
        profile_tokens
        & title_tokens
    )

    # Strong role terms
    role_keywords = {

        "software",
        "developer",
        "engineer",
        "data",
        "analyst",
        "scientist",
        "machine",
        "learning",
        "ai",
        "python",
        "java",
        "backend",
        "frontend",
        "full",
        "stack",
        "cloud",
        "devops",
        "cybersecurity",
        "embedded",
        "electronics",
        "civil",
        "mechanical",
        "design",
        "manufacturing",
        "automation",
        "qa"
    }

    role_common = (
        common
        & role_keywords
    )

    if not role_common:
        return 0.0

    return min(
        100.0,
        (
            len(role_common)
            / max(
                len(
                    title_tokens
                    & role_keywords
                ),
                1
            )
        ) * 100
    )


def calculate_branch_match(
    job,
    branch
):
    """
    Branch compatibility score.
    """

    job_text = clean_text(
        " ".join(
            [
                str(
                    job.get(
                        "job_title",
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
                        "job_description",
                        ""
                    )
                )
            ]
        )
    )

    if matches_branch(
        job_text,
        branch
    ):
        return 100.0

    return 0.0


# ============================================================
# EXTRACT EXPERIENCE YEARS
# ============================================================

def extract_experience_years(value):

    if value is None:
        return None

    # Handle list / array values
    if isinstance(
        value,
        (list, tuple, set)
    ):
        value = " ".join(
            str(x)
            for x in value
        )

    elif hasattr(
        value,
        "tolist"
    ) and not isinstance(
        value,
        (str, bytes)
    ):
        try:
            value = value.tolist()

            if isinstance(
                value,
                list
            ):
                value = " ".join(
                    str(x)
                    for x in value
                )

        except Exception:
            value = str(value)

    value = clean_text(
        value
    )

    if not value:
        return None

    # --------------------------------------------------------
    # 3+ years
    # --------------------------------------------------------

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*\+",
        value
    )

    if match:

        return float(
            match.group(1)
        )

    # --------------------------------------------------------
    # 2-5 years
    # --------------------------------------------------------

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)",
        value
    )

    if match:

        return float(
            match.group(1)
        )

    # --------------------------------------------------------
    # 2 years
    # --------------------------------------------------------

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        value
    )

    if match:

        return float(
            match.group(1)
        )

    return None


def calculate_experience_match(
    profile,
    job
):
    """
    Experience compatibility.

    Final-year students are treated as
    approximately 0 years professional experience.
    """

    student_experience = profile.get(
        "experience",
        ""
    ) if profile else ""

    student_years = extract_experience_years(
        student_experience
    )

    if student_years is None:
        student_years = 0.0

    job_experience = job.get(
        "experience",
        ""
    )

    required_years = extract_experience_years(
        job_experience
    )

    if required_years is None:
        return 50.0

    if student_years >= required_years:
        return 100.0

    difference = (
        required_years
        - student_years
    )

    if difference <= 1:
        return 80.0

    if difference <= 2:
        return 60.0

    if difference <= 3:
        return 35.0

    return 10.0


def calculate_location_match(
    profile,
    job
):
    """
    Location compatibility.

    Exact location match = 100
    Remote job = 100
    Same city = 100
    Otherwise = 25
    """

    if not profile:
        return 25.0

    student_location = clean_text(
        profile.get(
            "location",
            ""
        )
    )

    job_location = clean_text(
        job.get(
            "location",
            ""
        )
    )

    work_mode = clean_text(
        job.get(
            "work_mode",
            ""
        )
    )

    if "remote" in work_mode:
        return 100.0

    if not student_location:
        return 25.0

    if not job_location:
        return 25.0

    student_parts = set(
        student_location.replace(
            ",",
            " "
        ).split()
    )

    job_parts = set(
        job_location.replace(
            ",",
            " "
        ).split()
    )

    if student_parts & job_parts:
        return 100.0

    return 25.0


def calculate_live_match_score(
    profile,
    job,
    branch
):
    """
    Final Live Job AI Match Score.

    Weights:
        Skills       = 45%
        Role         = 25%
        Branch       = 15%
        Experience   = 10%
        Location     = 5%
    """

    student_skills = (
        extract_student_skills(
            profile
        )
    )

    job_skills = (
        extract_job_skills(
            job
        )
    )

    skills_score = (
        calculate_skills_match(
            student_skills,
            job_skills
        )
    )

    role_score = (
        calculate_role_match(
            profile,
            job
        )
    )

    branch_score = (
        calculate_branch_match(
            job,
            branch
        )
    )

    experience_score = (
        calculate_experience_match(
            profile,
            job
        )
    )

    location_score = (
        calculate_location_match(
            profile,
            job
        )
    )

    final_score = (

        skills_score * 0.45

        + role_score * 0.25

        + branch_score * 0.15

        + experience_score * 0.10

        + location_score * 0.05
    )

    return {

        "match_score":
            round(
                final_score,
                2
            ),

        "skills_match":
            round(
                skills_score,
                2
            ),

        "role_match":
            round(
                role_score,
                2
            ),

        "branch_match":
            round(
                branch_score,
                2
            ),

        "experience_match":
            round(
                experience_score,
                2
            ),

        "location_match":
            round(
                location_score,
                2
            )
    }


def recommend_live_jobs(
    jobs_df,
    student_profile,
    branch,
    top_n=10
):
    """
    Rank live company openings using
    explainable multi-factor AI matching.
    """

    if jobs_df.empty:
        return pd.DataFrame()

    results = []

    for _, job in jobs_df.iterrows():

        job_dict = job.to_dict()

        scores = (
            calculate_live_match_score(
                student_profile,
                job_dict,
                branch
            )
        )

        job_dict.update(
            scores
        )

        results.append(
            job_dict
        )

    result_df = pd.DataFrame(
        results
    )

    return (
        result_df
        .sort_values(
            by="match_score",
            ascending=False
        )
        .head(top_n)
        .copy()
    )

# ============================================================
# DISPLAY REFERENCE JOB
# ============================================================

def display_reference_job(job):

    company = job.get(
        "company_name",
        "Unknown Company"
    )

    title = job.get(
        "title",
        "Unknown Role"
    )

    location = job.get(
        "location",
        "Not specified"
    )

    experience = job.get(
        "experience",
        "Not specified"
    )

    skills = job.get(
        "skills",
        "Not specified"
    )

    score = float(
        job.get(
            "match_score",
            0
        )
    )

    with st.container(
        border=True
    ):

        st.markdown(
            f"### 💼 {title}"
        )

        st.write(
            f"🏢 **Company:** {company}"
        )

        st.write(
            f"📍 **Location:** {location}"
        )

        st.write(
            f"🧑‍💻 **Experience:** {experience}"
        )

        st.write(
            f"🛠️ **Skills:** {skills}"
        )

        st.progress(
            min(score / 100, 1.0),
            text=(
                f"AI Match Score: "
                f"{score:.1f}%"
            )
        )

        st.caption(
            "Source: 97K reference job dataset"
        )




# ============================================================
# IN-PORTAL APPLICATION FORM
# ============================================================

def show_live_application_form(job):

    live_job_id = job.get("id")

    company = job.get(
        "company_name",
        "Unknown Company"
    )

    title = job.get(
        "job_title",
        "Unknown Role"
    )

    if pd.isna(live_job_id):
        st.error("Unable to apply: live job ID is missing.")
        return

    live_job_id = int(live_job_id)

    st.markdown("#### 🚀 Apply for this position")

    with st.form(
        key=f"application_form_{live_job_id}"
    ):

        st.write(
            f"**{title}** at **{company}**"
        )

        cover_letter = st.text_area(
            "Cover Letter",
            placeholder=(
                "Write a short cover letter..."
            ),
            key=f"cover_letter_{live_job_id}"
        )

        resume_file = st.file_uploader(
        "📄 Upload Resume *",
        type=["pdf", "doc", "docx"],
        key=f"resume_upload_{live_job_id}"
    )

        resume_filename = None

        if resume_file is not None:
            resume_filename = resume_file.name
            st.success(
                f"✅ Resume uploaded: {resume_filename}"
            )
        else:
            st.warning(
                "⚠️ Resume is mandatory to submit an application."
            )
        submitted = st.form_submit_button(
            "🚀 Submit Application",
            width="stretch"
        )

        if submitted:

            access_token = (
                st.session_state.get(
                    "access_token"
                )
            )

            if not access_token:

                            st.error(
                                "Your session has expired. "
                                "Please login again."
                            )

                            return

            if not resume_filename:

                            st.error(
                                "❌ Resume is mandatory. "
                                "Please upload your resume."
                            )

                            return

                       

            from api.client import APIClient

            api_client = APIClient()

            api_client.set_token(
                access_token
            )

            # ------------------------------------------------
            # UPLOAD RESUME
            # ------------------------------------------------

            if resume_file is None:
                st.error(
                    "❌ Resume is mandatory to submit an application."
                )
                return

            resume_upload_response = api_client.upload_resume(
                file_name=resume_file.name,
                file_data=resume_file.getvalue(),
                mime_type=resume_file.type
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
                st.error(
                    "❌ Resume uploaded but resume ID was not returned."
                )
                return

            # ------------------------------------------------
            # SUBMIT APPLICATION
            # ------------------------------------------------

            response = api_client.apply_for_job(
                job_id=None,
                live_job_id=live_job_id,
                cover_letter=cover_letter,
                resume_filename=resume_file.name,
                resume_id=resume_id
            )
            if response.status_code == 201:

                st.success(
                    "✅ Application submitted successfully!"
                )

                st.info(
                    "Your application is now available "
                    "in My Applications."
                )

                st.session_state[
                    "application_submitted"
                ] = True

            elif response.status_code == 400:

                try:
                    detail = response.json().get(
                        "detail",
                        "You have already applied for this job."
                    )
                except Exception:
                    detail = (
                        "You have already applied for this job."
                    )

                st.warning(
                    f"⚠️ {detail}"
                )

            else:

                try:
                    detail = response.json().get(
                        "detail",
                        "Application failed."
                    )
                except Exception:
                    detail = (
                        "Application failed."
                    )

                st.error(
                    f"❌ {detail}"
                )
# ============================================================
# DISPLAY LIVE JOB
# ============================================================

def display_live_job(job):

    company = job.get(
        "company_name",
        "Unknown Company"
    )

    title = job.get(
        "job_title",
        "Unknown Role"
    )

    location = job.get(
        "location",
        "Not specified"
    )

    experience = job.get(
        "experience",
        "Not specified"
    )

    skills = job.get(
        "skills",
        "Not specified"
    )

    work_mode = job.get(
        "work_mode",
        "Not specified"
    )

    source = job.get(
        "source",
        "Company Career Source"
    )

    url = str(
        job.get(
            "application_url",
            ""
        )
    ).strip()

    score = float(
        job.get(
            "match_score",
            0
        )
    )

    # --------------------------------------------------------
    # MATCH BREAKDOWN
    # --------------------------------------------------------

    skills_match = float(
        job.get(
            "skills_match",
            0
        )
    )

    role_match = float(
        job.get(
            "role_match",
            0
        )
    )

    branch_match = float(
        job.get(
            "branch_match",
            0
        )
    )

    experience_match = float(
        job.get(
            "experience_match",
            0
        )
    )

    location_match = float(
        job.get(
            "location_match",
            0
        )
    )

    # ========================================================
    # JOB CARD
    # ========================================================

    with st.container(
        border=True
    ):

        st.markdown(
            f"### 🔥 {title}"
        )

        st.write(
            f"🏢 **Company:** {company}"
        )

        st.write(
            f"📍 **Location:** {location}"
        )

        st.write(
            f"🧑‍💻 **Experience:** {experience}"
        )

        st.write(
            f"🛠️ **Skills:** {skills}"
        )

        st.write(
            f"💻 **Work Mode:** {work_mode}"
        )

        st.write(
            f"🔗 **Source:** {source}"
        )

        # ----------------------------------------------------
        # AI MATCH SCORE
        # ----------------------------------------------------

        st.progress(
            min(
                score / 100,
                1.0
            ),
            text=(
                f"🤖 AI Match Score: "
                f"{score:.1f}%"
            )
        )

        # ----------------------------------------------------
        # MATCH BREAKDOWN
        # ----------------------------------------------------

        st.markdown(
            "#### 📊 AI Match Breakdown"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "🛠️ Skills",
                f"{skills_match:.0f}%"
            )

        with col2:

            st.metric(
                "🎯 Role",
                f"{role_match:.0f}%"
            )

        with col3:

            st.metric(
                "🎓 Branch",
                f"{branch_match:.0f}%"
            )

        col4, col5 = st.columns(2)

        with col4:

            st.metric(
                "🧑‍💻 Experience",
                f"{experience_match:.0f}%"
            )

        with col5:

            st.metric(
                "📍 Location",
                f"{location_match:.0f}%"
            )

        # ----------------------------------------------------
        # SAVE + APPLY BUTTONS
        # ----------------------------------------------------

        live_job_id = job.get("id")

        if pd.notna(live_job_id):

            live_job_id = int(live_job_id)

            api_client = get_api_client()

            save_col, apply_col = st.columns(2)

            # ------------------------------------------------
            # SAVE JOB
            # ------------------------------------------------

            with save_col:

                save_key = f"save_live_job_{live_job_id}"

                if st.button(
                        "💾 Save Job",
                        key=f"save_job_{live_job_id}",
                        use_container_width=True
                    ):

                        api_client = APIClient()

                        token = st.session_state.get("access_token")

                        if token:
                            api_client.set_token(token)

                        response = api_client.save_job(
                            live_job_id=int(live_job_id)
                        )
                    

                        if response.status_code in (200, 201):

                            st.success("✅ Job saved successfully.")

                        elif response.status_code == 400:

                            try:
                                detail = response.json().get(
                                    "detail",
                                    "Job already saved."
                                )
                            except Exception:
                                detail = "Job already saved."

                            st.warning(f"⚠️ {detail}")

                        elif response.status_code == 401:

                            st.error(
                                "❌ Your session has expired. Please login again."
                            )

                        else:

                            try:
                                detail = response.json().get(
                                    "detail",
                                    "Unable to save job."
                                )
                            except Exception:
                                detail = "Unable to save job."

                            st.error(
                                f"❌ {detail}"
                            )

            # ------------------------------------------------
            # APPLY JOB
            # ------------------------------------------------

            with apply_col:

                apply_key = f"apply_live_job_{live_job_id}"

                if st.button(
                    "🚀 Apply Now",
                    key=apply_key,
                    width="stretch"
                ):

                    st.session_state[
                        "selected_application_job"
                    ] = job.to_dict()

                # --------------------------------------------------------
                # APPLICATION FORM
                # --------------------------------------------------------

                selected_job = st.session_state.get(
                    "selected_application_job"
                )

                if selected_job:

                    selected_id = selected_job.get("id")

                    if (
                        pd.notna(selected_id)
                        and int(selected_id) == int(live_job_id)
                    ):

                        show_live_application_form(
                            selected_job
                        )

            # ----------------------------------------------------
            # LIVE STATUS
            # ----------------------------------------------------

            st.success(
                "LIVE OPENING — "
                "verified from company career source"
            )


# ============================================================
# MAIN PAGE
# ============================================================

# ============================================================
# LIVE RECOMMENDED JOBS PAGE
# ============================================================

def show_recommended_jobs(student_profile=None):

    st.title("🔥 Live Recommended Openings")

    st.markdown(
        """
        Current company job openings matched against
        your profile using AI-powered profile matching.
        """
    )

    # --------------------------------------------------------
    # GET STUDENT PROFILE
    # --------------------------------------------------------

    if student_profile is None:

        student_profile = (
            st.session_state.get(
                "student_profile",
                {}
            )
        )

    # --------------------------------------------------------
    # GET BRANCH
    # --------------------------------------------------------

    branch = get_student_branch(
        student_profile
    )

    st.caption(
        f"🎓 Profile branch: {branch.upper()}"
    )

    # --------------------------------------------------------
    # LOAD LIVE JOBS
    # --------------------------------------------------------

    live_jobs = load_live_jobs()

    if live_jobs.empty:

        st.info(
            "No live company openings are currently available."
        )

        return

    # --------------------------------------------------------
    # AI MATCHING
    # --------------------------------------------------------

    live_recommendations = (
        recommend_live_jobs(
            live_jobs,
            student_profile,
            branch,
            top_n=20
        )
    )

    if live_recommendations.empty:

        st.warning(
            "No live openings currently match "
            "your branch and profile."
        )

        return

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    st.success(
        f"Found {len(live_recommendations)} "
        "live openings matching your profile."
    )

    st.divider()

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    for _, job in (
        live_recommendations.iterrows()
    ):

        display_live_job(
            job
        )

# ============================================================
# OPTIONAL DIRECT RUN
# ============================================================

if __name__ == "__main__":

    show_recommended_jobs()