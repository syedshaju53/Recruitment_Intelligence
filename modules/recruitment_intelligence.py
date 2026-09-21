# ============================================================
# AI-POWERED RECRUITMENT INTELLIGENCE
# ATS-BACKED STREAMLIT MODULE
# ============================================================

import os
import re
from pathlib import Path
from urllib.parse import quote_plus
import requests

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine, text


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Recruitment Intelligence",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

MARKET_DATA_PATHS = [
    DATA_DIR / "indian-job-market-dataset-2025.xlsx",
    BASE_DIR / "indian-job-market-dataset-2025.xlsx",
    DATA_DIR / "raw" / "indian-job-market-dataset-2025.xlsx",
]


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_NAME = os.environ.get("POSTGRES_DB", "recruitment_db")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD")


# ============================================================
# DATABASE ENGINE
# ============================================================

@st.cache_resource
def get_database_engine():

    if not DB_PASSWORD:
        return None

    database_url = (
        f"postgresql+psycopg2://"
        f"{quote_plus(DB_USER)}:"
        f"{quote_plus(DB_PASSWORD)}@"
        f"{DB_HOST}:"
        f"{DB_PORT}/"
        f"{DB_NAME}"
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


# ============================================================
# CONSTANTS
# ============================================================

TARGET_BRANCHES = [
    "CSE",
    "ECE",
    "Civil",
    "Mechanical",
]


ACADEMIC_KEYWORDS = [
    "lecturer",
    "professor",
    "teacher",
    "teaching",
    "tutor",
    "trainer",
    "instructor",
    "faculty",
    "academic",
    "education",
    "school teacher",
    "college lecturer",
    "university lecturer",
]


NON_TECHNICAL_KEYWORDS = [
    "sales",
    "sales executive",
    "sales manager",
    "marketing",
    "digital marketing",
    "business development",
    "business development executive",
    "hr executive",
    "human resources",
    "recruiter",
    "recruitment",
    "talent acquisition",
    "finance",
    "financial analyst",
    "accountant",
    "accounting",
    "insurance sales",
    "telecaller",
    "customer service",
    "customer support",
    "relationship manager",
    "content writer",
    "copywriter",
    "legal",
    "lawyer",
    "operations executive",
]


# ============================================================
# CSE KEYWORDS
# ============================================================

CSE_KEYWORDS = [
    "software",
    "software engineer",
    "software developer",
    "software development",
    "developer",
    "development",
    "programmer",
    "data analyst",
    "data engineer",
    "data scientist",
    "data science",
    "machine learning",
    "machine learning engineer",
    "artificial intelligence",
    "ai engineer",
    "ai developer",
    "deep learning",
    "nlp",
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "nodejs",
    "full stack",
    "fullstack",
    "frontend",
    "front end",
    "backend",
    "back end",
    "web developer",
    "web development",
    "cloud",
    "cloud engineer",
    "cloudops",
    "devops",
    "devsecops",
    "cybersecurity",
    "cyber security",
    "security engineer",
    "penetration testing",
    "network engineer",
    "database",
    "database engineer",
    "sql",
    "qa engineer",
    "quality assurance",
    "test automation",
    "automation engineer",
    "platform engineer",
    "site reliability",
    "sre",
    "systems engineer",
    "application engineer",
    "technical engineer",
    "technical analyst",
    "technical support engineer",
    "solutions engineer",
    "product engineer",
    "servicenow",
    ".net",
    "golang",
    "go developer",
    "ruby",
    "php",
    "api",
]


# ============================================================
# ECE KEYWORDS
# ============================================================

ECE_KEYWORDS = [
    "embedded",
    "embedded systems",
    "electronics",
    "electronics engineer",
    "firmware",
    "hardware engineer",
    "hardware",
    "vlsi",
    "asic",
    "fpga",
    "semiconductor",
    "pcb",
    "pcb design",
    "iot",
    "internet of things",
    "telecom",
    "telecommunication",
    "rf engineer",
    "radio frequency",
    "microcontroller",
    "microprocessor",
    "electronic design",
    "electronics design",
    "verification engineer",
    "validation engineer",
    "device engineer",
    "devices engineer",
    "signal processing",
    "embedded software",
]


# ============================================================
# CIVIL KEYWORDS
# ============================================================

CIVIL_KEYWORDS = [
    "civil engineer",
    "civil engineering",
    "structural engineer",
    "structural engineering",
    "construction engineer",
    "construction",
    "site engineer",
    "site engineering",
    "planning engineer",
    "quantity surveyor",
    "quantity surveying",
    "bim",
    "building information modeling",
    "autocad",
    "geotechnical",
    "geotechnical engineer",
    "transportation engineer",
    "highway engineer",
    "infrastructure engineer",
    "project engineer",
    "civil design",
    "construction planning",
    "estimator",
    "civil estimator",
]


# ============================================================
# MECHANICAL KEYWORDS
# ============================================================

MECHANICAL_KEYWORDS = [
    "mechanical engineer",
    "mechanical engineering",
    "mechanical design",
    "manufacturing engineer",
    "manufacturing",
    "production engineer",
    "production",
    "automotive engineer",
    "automotive",
    "cad engineer",
    "cad",
    "solidworks",
    "catia",
    "creo",
    "ansys",
    "hvac",
    "maintenance engineer",
    "maintenance",
    "quality engineer",
    "industrial engineer",
    "industrial engineering",
    "process engineer",
    "thermal engineer",
    "thermal",
    "tooling engineer",
    "tooling",
    "mechatronics",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_text(value):
    """Convert any value to a safe lowercase string."""

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    return str(value).strip().lower()


def combine_job_text(row):
    """Combine relevant ATS fields for classification."""

    fields = [
        row.get("job_title", ""),
        row.get("department", ""),
        row.get("skills", ""),
        row.get("job_description", ""),
    ]

    return " ".join(
        safe_text(value)
        for value in fields
    )


def contains_keyword(text_value, keywords):
    """Check whether text contains any keyword."""

    value = safe_text(text_value)

    return any(
        keyword.lower() in value
        for keyword in keywords
    )


def is_academic_job(row):
    """Identify academic / teaching jobs."""

    text_value = combine_job_text(row)

    return contains_keyword(
        text_value,
        ACADEMIC_KEYWORDS,
    )


def is_nontechnical_job(row):
    """Identify nontechnical corporate roles."""

    title = safe_text(
        row.get("job_title", "")
    )

    for keyword in NON_TECHNICAL_KEYWORDS:

        if keyword.lower() in title:
            return True

    return False


# ============================================================
# BRANCH DETECTION
# ============================================================

def detect_branch(row):
    """
    Classify ATS opening into
    CSE / ECE / Civil / Mechanical.
    """

    title = safe_text(
        row.get("job_title", "")
    )

    department = safe_text(
        row.get("department", "")
    )

    skills = safe_text(
        row.get("skills", "")
    )

    description = safe_text(
        row.get("job_description", "")
    )

    title_department = (
        f"{title} {department}"
    )

    # --------------------------------------------------------
    # CIVIL
    # --------------------------------------------------------

    if contains_keyword(
        title_department,
        CIVIL_KEYWORDS,
    ):
        return "Civil"

    # --------------------------------------------------------
    # MECHANICAL
    # --------------------------------------------------------

    if contains_keyword(
        title_department,
        MECHANICAL_KEYWORDS,
    ):
        return "Mechanical"

    # --------------------------------------------------------
    # ECE
    # --------------------------------------------------------

    if contains_keyword(
        title_department,
        ECE_KEYWORDS,
    ):
        return "ECE"

    # --------------------------------------------------------
    # CSE
    # --------------------------------------------------------

    if contains_keyword(
        title_department,
        CSE_KEYWORDS,
    ):
        return "CSE"

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    combined = (
        f"{skills} {description}"
    )

    if contains_keyword(
        combined,
        CIVIL_KEYWORDS,
    ):
        return "Civil"

    if contains_keyword(
        combined,
        MECHANICAL_KEYWORDS,
    ):
        return "Mechanical"

    if contains_keyword(
        combined,
        ECE_KEYWORDS,
    ):
        return "ECE"

    if contains_keyword(
        combined,
        CSE_KEYWORDS,
    ):
        return "CSE"

    return None


# ============================================================
# FILTER TARGET JOBS
# ============================================================

def filter_target_jobs(df):
    """Keep only target engineering/company jobs."""

    if df.empty:
        return df.copy()

    working = df.copy()

    working["branch"] = working.apply(
        detect_branch,
        axis=1,
    )

    working["academic_flag"] = working.apply(
        is_academic_job,
        axis=1,
    )

    working["nontechnical_flag"] = working.apply(
        is_nontechnical_job,
        axis=1,
    )

    working = working[
        working["branch"].isin(
            TARGET_BRANCHES
        )
    ]

    working = working[
        ~working["academic_flag"]
    ]

    working = working[
        ~working["nontechnical_flag"]
    ]

    return working.copy()


# ============================================================
# JOB KEY
# ============================================================

def job_key(row):
    """
    Create stable job identifier.

    Prefer source_job_id.
    Fall back to job_id.
    """

    source = safe_text(
        row.get("source", "")
    )

    source_job_id = safe_text(
        row.get("source_job_id", "")
    )

    job_id = safe_text(
        row.get("job_id", "")
    )

    if source_job_id:

        return (
            f"{source}:{source_job_id}"
        )

    if job_id:

        return (
            f"{source}:{job_id}"
        )

    return (
        f"{source}:"
        f"{safe_text(row.get('company_name', ''))}:"
        f"{safe_text(row.get('job_title', ''))}"
    )


# ============================================================
# DEDUPLICATE JOBS
# ============================================================

def deduplicate_jobs(df):
    """Deduplicate ATS openings."""

    if df.empty:
        return df.copy()

    result = df.copy()

    result["_job_key"] = result.apply(
        job_key,
        axis=1,
    )

    result = result.drop_duplicates(
        subset=["_job_key"],
        keep="first",
    )

    return result.drop(
        columns=["_job_key"],
        errors="ignore",
    )


# ============================================================
# ACTIVITY INDEX
# ============================================================

def calculate_activity_index(
    current_openings,
    historical_jobs,
):
    """
    Calculate a descriptive recruitment
    activity index.

    This is NOT hiring probability.
    """

    if (
        current_openings <= 0
        and historical_jobs <= 0
    ):
        return 0.0

    current_component = min(
        float(current_openings) / 100.0,
        1.0,
    )

    history_component = min(
        float(historical_jobs) / 200.0,
        1.0,
    )

    score = (
        current_component * 60
        +
        history_component * 40
    )

    return round(
        score,
        1,
    )


# ============================================================
# LOAD CURRENT ATS JOBS
# ============================================================

@st.cache_data(ttl=60)
def load_current_ats_jobs():

    engine = get_database_engine()

    if engine is None:
        return pd.DataFrame()

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
            source_job_id,
            status,
            last_checked
        FROM live_jobs
        WHERE LOWER(
            COALESCE(status, '')
        ) IN (
            'open',
            'active',
            'hiring',
            'ongoing'
        )
        ORDER BY
            COALESCE(
                updated_date,
                posted_date,
                last_checked
            ) DESC NULLS LAST
        """
    )

    try:

        with engine.connect() as connection:

            df = pd.read_sql(
                query,
                connection,
            )

        if df.empty:
            return df

        for column in [
            "posted_date",
            "updated_date",
            "last_checked",
        ]:

            if column in df.columns:

                df[column] = pd.to_datetime(
                    df[column],
                    errors="coerce",
                )

        return filter_target_jobs(
            df
        )

    except Exception as error:

        st.error(
            f"Unable to load current ATS jobs: {error}"
        )

        return pd.DataFrame()


# ============================================================
# LOAD ATS HISTORY
# ============================================================

@st.cache_data(ttl=60)
def load_ats_history():

    engine = get_database_engine()

    if engine is None:
        return pd.DataFrame()

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
            application_url,
            source,
            source_job_id,
            status,
            observed_at,
            first_seen_at,
            last_seen_at,
            closed_at,
            collection_run_id
        FROM job_history
        ORDER BY observed_at DESC
        """
    )

    try:

        with engine.connect() as connection:

            df = pd.read_sql(
                query,
                connection,
            )

        if df.empty:
            return df

        for column in [
            "observed_at",
            "first_seen_at",
            "last_seen_at",
            "closed_at",
        ]:

            if column in df.columns:

                df[column] = pd.to_datetime(
                    df[column],
                    errors="coerce",
                )

        return filter_target_jobs(
            df
        )

    except Exception as error:

        st.error(
            f"Unable to load ATS history: {error}"
        )

        return pd.DataFrame()


# ============================================================
# COLLECTION RUN SUMMARY
# ============================================================

def build_collection_run_summary(
    history_df,
):

    if history_df.empty:
        return pd.DataFrame()

    working = history_df.copy()

    working["_job_key"] = working.apply(
        job_key,
        axis=1,
    )

    if (
        "collection_run_id"
        not in working.columns
    ):

        working["collection_run_id"] = (
            working["observed_at"]
            .dt.strftime(
                "%Y%m%d%H%M%S"
            )
        )

    summary = (
        working
        .groupby(
            "collection_run_id"
        )
        .agg(
            run_started=(
                "observed_at",
                "min",
            ),
            openings=(
                "_job_key",
                "nunique",
            ),
            companies=(
                "company_name",
                "nunique",
            ),
            roles=(
                "job_title",
                "nunique",
            ),
        )
        .reset_index()
        .sort_values(
            "run_started"
        )
    )

    return summary


# ============================================================
# MONTHLY ATS ACTIVITY
# ============================================================

def build_monthly_activity(
    history_df,
):

    if history_df.empty:
        return pd.DataFrame()

    working = history_df.copy()

    working = working[
        working["observed_at"].notna()
    ]

    if working.empty:
        return pd.DataFrame()

    working["_job_key"] = working.apply(
        job_key,
        axis=1,
    )

    working["month"] = (
        working["observed_at"]
        .dt.to_period("M")
        .astype(str)
    )

    summary = (
        working
        .groupby("month")
        .agg(
            openings=(
                "_job_key",
                "nunique",
            ),
            companies=(
                "company_name",
                "nunique",
            ),
            roles=(
                "job_title",
                "nunique",
            ),
        )
        .reset_index()
        .sort_values("month")
    )

    return summary


# ============================================================
# COMPANY INTELLIGENCE
# ============================================================

def build_company_intelligence(
    current_df,
    history_df,
):

    if current_df.empty:
        return pd.DataFrame()

    current = current_df.copy()

    current["_job_key"] = current.apply(
        job_key,
        axis=1,
    )

    company_current = (
        current
        .groupby("company_name")
        .agg(
            current_openings=(
                "_job_key",
                "nunique",
            ),
            current_roles=(
                "job_title",
                "nunique",
            ),
            current_locations=(
                "location",
                "nunique",
            ),
        )
        .reset_index()
    )

    if history_df.empty:

        company_current[
            "historical_jobs"
        ] = 0

    else:

        history = history_df.copy()

        history["_job_key"] = history.apply(
            job_key,
            axis=1,
        )

        historical = (
            history
            .groupby("company_name")
            .agg(
                historical_jobs=(
                    "_job_key",
                    "nunique",
                )
            )
            .reset_index()
        )

        company_current = (
            company_current.merge(
                historical,
                on="company_name",
                how="left",
            )
        )

        company_current[
            "historical_jobs"
        ] = (
            company_current[
                "historical_jobs"
            ]
            .fillna(0)
        )

    company_current[
        "activity_index"
    ] = company_current.apply(
        lambda row:
            calculate_activity_index(
                row["current_openings"],
                row["historical_jobs"],
            ),
        axis=1,
    )

    return company_current.sort_values(
        "current_openings",
        ascending=False,
    )


# ============================================================
# ROLE INTELLIGENCE
# ============================================================

def build_role_intelligence(
    current_df,
):

    if current_df.empty:
        return pd.DataFrame()

    working = current_df.copy()

    working["_job_key"] = working.apply(
        job_key,
        axis=1,
    )

    summary = (
        working
        .groupby(
            [
                "job_title",
                "branch",
            ]
        )
        .agg(
            openings=(
                "_job_key",
                "nunique",
            ),
            companies=(
                "company_name",
                "nunique",
            ),
            locations=(
                "location",
                "nunique",
            ),
        )
        .reset_index()
        .sort_values(
            "openings",
            ascending=False,
        )
    )

    return summary


# ============================================================
# BRANCH INTELLIGENCE
# ============================================================

def build_branch_intelligence(
    current_df,
):

    if current_df.empty:
        return pd.DataFrame()

    working = current_df.copy()

    working["_job_key"] = working.apply(
        job_key,
        axis=1,
    )

    summary = (
        working
        .groupby("branch")
        .agg(
            openings=(
                "_job_key",
                "nunique",
            ),
            companies=(
                "company_name",
                "nunique",
            ),
            roles=(
                "job_title",
                "nunique",
            ),
            locations=(
                "location",
                "nunique",
            ),
        )
        .reset_index()
        .sort_values(
            "openings",
            ascending=False,
        )
    )

    return summary


# ============================================================
# LOCATION INTELLIGENCE
# ============================================================

def build_location_intelligence(
    current_df,
):

    if current_df.empty:
        return pd.DataFrame()

    working = current_df.copy()

    working["_job_key"] = working.apply(
        job_key,
        axis=1,
    )

    summary = (
        working
        .groupby("location")
        .agg(
            openings=(
                "_job_key",
                "nunique",
            ),
            companies=(
                "company_name",
                "nunique",
            ),
        )
        .reset_index()
        .sort_values(
            "openings",
            ascending=False,
        )
    )

    return summary


# ============================================================
# LOAD 97K MARKET DATASET
# ============================================================

@st.cache_data(ttl=3600)
def load_market_dataset():

    for path in MARKET_DATA_PATHS:

        if path.exists():

            try:

                return pd.read_excel(
                    path
                )

            except Exception:

                continue

    return pd.DataFrame()


# ============================================================
# MARKET DATA PREPARATION
# ============================================================

def prepare_market_dataset(df):

    if df.empty:
        return df.copy()

    working = df.copy()

    working.columns = [
        str(column).strip()
        for column in working.columns
    ]

    # --------------------------------------------------------
    # Salary midpoint
    # --------------------------------------------------------

    if (
        "minimumSalary"
        in working.columns
        and
        "maximumSalary"
        in working.columns
    ):

        working[
            "salary_midpoint"
        ] = (
            pd.to_numeric(
                working[
                    "minimumSalary"
                ],
                errors="coerce",
            )
            +
            pd.to_numeric(
                working[
                    "maximumSalary"
                ],
                errors="coerce",
            )
        ) / 2

    # --------------------------------------------------------
    # Experience midpoint
    # --------------------------------------------------------

    if (
        "minimumExperience"
        in working.columns
        and
        "maximumExperience"
        in working.columns
    ):

        working[
            "experience_midpoint"
        ] = (
            pd.to_numeric(
                working[
                    "minimumExperience"
                ],
                errors="coerce",
            )
            +
            pd.to_numeric(
                working[
                    "maximumExperience"
                ],
                errors="coerce",
            )
        ) / 2

    # --------------------------------------------------------
    # Skill count
    # --------------------------------------------------------

    if "tagsAndSkills" in working.columns:

        working["skill_count"] = (
            working[
                "tagsAndSkills"
            ]
            .fillna("")
            .astype(str)
            .apply(
                lambda value:
                    len(
                        [
                            item
                            for item in re.split(
                                r"[,|;/]",
                                value,
                            )
                            if item.strip()
                        ]
                    )
            )
        )

    # --------------------------------------------------------
    # Remote flag
    # --------------------------------------------------------

    if "location" in working.columns:

        working["is_remote"] = (
            working[
                "location"
            ]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(
                "remote|work from home|wfh",
                regex=True,
            )
            .astype(int)
        )

    # --------------------------------------------------------
    # Title length
    # --------------------------------------------------------

    if "title" in working.columns:

        working["title_length"] = (
            working[
                "title"
            ]
            .fillna("")
            .astype(str)
            .str.len()
        )

    # --------------------------------------------------------
    # Company name length
    # --------------------------------------------------------

    if (
        "companyName"
        in working.columns
    ):

        working[
            "company_name_length"
        ] = (
            working[
                "companyName"
            ]
            .fillna("")
            .astype(str)
            .str.len()
        )

    return working


# ============================================================
# MARKET DEMAND ANALYSIS
# ============================================================

def calculate_market_demand(df):

    if df.empty:
        return pd.DataFrame()

    if "title" not in df.columns:
        return pd.DataFrame()

    working = df.copy()

    working["title_text"] = (
        working["title"]
        .fillna("")
        .astype(str)
        .str.lower()
    )

    academic_pattern = "|".join(
        re.escape(keyword)
        for keyword in ACADEMIC_KEYWORDS
    )

    nontechnical_pattern = "|".join(
        re.escape(keyword)
        for keyword in NON_TECHNICAL_KEYWORDS
    )

    working = working[
        ~working[
            "title_text"
        ].str.contains(
            academic_pattern,
            regex=True,
            na=False,
        )
    ]

    working = working[
        ~working[
            "title_text"
        ].str.contains(
            nontechnical_pattern,
            regex=True,
            na=False,
        )
    ]

    # --------------------------------------------------------
    # Market branch classification
    # --------------------------------------------------------

    def market_branch(title):

        text_value = safe_text(
            title
        )

        if contains_keyword(
            text_value,
            CIVIL_KEYWORDS,
        ):
            return "Civil"

        if contains_keyword(
            text_value,
            MECHANICAL_KEYWORDS,
        ):
            return "Mechanical"

        if contains_keyword(
            text_value,
            ECE_KEYWORDS,
        ):
            return "ECE"

        if contains_keyword(
            text_value,
            CSE_KEYWORDS,
        ):
            return "CSE"

        return None

    working["branch"] = (
        working["title"]
        .apply(market_branch)
    )

    working = working[
        working["branch"].isin(
            TARGET_BRANCHES
        )
    ]

    if working.empty:
        return pd.DataFrame()

    # --------------------------------------------------------
    # Demand aggregation
    # --------------------------------------------------------

    summary = (
        working
        .groupby("branch")
        .agg(
            postings=(
                "title",
                "count",
            ),
            companies=(
                "companyName",
                "nunique",
            )
            if "companyName"
            in working.columns
            else (
                "title",
                "count",
            ),
            locations=(
                "location",
                "nunique",
            )
            if "location"
            in working.columns
            else (
                "title",
                "count",
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Min-Max normalization
    # --------------------------------------------------------

    def min_max(series):

        minimum = series.min()
        maximum = series.max()

        if maximum == minimum:

            return pd.Series(
                [100.0] * len(series),
                index=series.index,
            )

        return (
            (
                series
                - minimum
            )
            /
            (
                maximum
                - minimum
            )
            * 100
        )

    summary[
        "posting_score"
    ] = min_max(
        summary["postings"]
    )

    summary[
        "company_score"
    ] = min_max(
        summary["companies"]
    )

    summary[
        "location_score"
    ] = min_max(
        summary["locations"]
    )

    summary[
        "demand_score"
    ] = (
        summary[
            "posting_score"
        ] * 0.50
        +
        summary[
            "company_score"
        ] * 0.30
        +
        summary[
            "location_score"
        ] * 0.20
    )

    summary[
        "demand_score"
    ] = (
        summary[
            "demand_score"
        ]
        .round(2)
    )

    summary[
        "demand_class"
    ] = np.where(
        summary[
            "demand_score"
        ] >= 66,
        "High Demand",
        np.where(
            summary[
                "demand_score"
            ] >= 33,
            "Medium Demand",
            "Low Demand",
        ),
    )

    return summary.sort_values(
        "demand_score",
        ascending=False,
    )


# ============================================================
# ML PREDICTION
# ============================================================

def request_ml_prediction(
    payload,
):

    try:

        import os

        response = requests.post(
            
            f"{os.getenv('API_BASE_URL', 'http://127.0.0.1:8000')}/ml/predict",
            json=payload,
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    except Exception as error:

        return {
            "error": str(error)
        }


# ============================================================
# MAIN STREAMLIT PAGE
# ============================================================

def show_recruitment_intelligence():

    st.title(
        "📊 Recruitment Intelligence"
    )

    st.caption(
        "AI-powered recruitment intelligence using "
        "live company ATS openings, historical ATS snapshots, "
        "job-market analytics and machine learning."
    )

    # ========================================================
    # DATABASE CHECK
    # ========================================================

    if not DB_PASSWORD:

        st.warning(
            "POSTGRES_PASSWORD is not set. "
            "Set the environment variable before starting Streamlit."
        )

        st.code(
            "export POSTGRES_PASSWORD='YOUR_DATABASE_PASSWORD'"
        )

        st.stop()

    # ========================================================
    # LOAD DATA
    # ========================================================

    current_raw = (
        load_current_ats_jobs()
    )

    history_raw = (
        load_ats_history()
    )

    current_jobs = (
        deduplicate_jobs(
            current_raw
        )
    )

    history_jobs = (
        history_raw.copy()
    )

    # ========================================================
    # HEADER
    # ========================================================

    st.markdown(
        "### 🔴 Live ATS Recruitment Intelligence"
    )

    st.info(
        "Current openings and historical recruitment activity "
        "are sourced from company ATS/career systems. "
        "Historical records represent observed job openings, "
        "not confirmed historical hires."
    )

    # ========================================================
    # FILTERS
    # ========================================================

    filter_col1, filter_col2, filter_col3 = (
        st.columns(3)
    )

    with filter_col1:

        branch_options = [
            "All Branches",
            "CSE",
            "ECE",
            "Civil",
            "Mechanical",
        ]

        selected_branch = st.selectbox(
            "🎓 Department / Branch",
            branch_options,
        )

    # --------------------------------------------------------
    # Available years
    # --------------------------------------------------------

    available_years = []

    if (
        not history_jobs.empty
        and
        "observed_at"
        in history_jobs.columns
    ):

        years = (
            history_jobs[
                "observed_at"
            ]
            .dropna()
            .dt.year
            .unique()
            .tolist()
        )

        available_years = sorted(
            [
                int(year)
                for year in years
            ]
        )

    with filter_col2:

        year_options = [
            "All Years"
        ] + [
            str(year)
            for year in available_years
        ]

        selected_year = st.selectbox(
            "📅 Year",
            year_options,
        )

    with filter_col3:

        month_options = [
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
            "December",
        ]

        selected_month = st.selectbox(
            "📆 Month",
            month_options,
        )

    # ========================================================
    # APPLY CURRENT FILTER
    # ========================================================

    filtered_current = (
        current_jobs.copy()
    )

    if (
        selected_branch
        != "All Branches"
        and
        not filtered_current.empty
    ):

        filtered_current = (
            filtered_current[
                filtered_current[
                    "branch"
                ]
                == selected_branch
            ]
        )

    # ========================================================
    # APPLY HISTORY FILTER
    # ========================================================

    filtered_history = (
        history_jobs.copy()
    )

    if not filtered_history.empty:

        if (
            selected_branch
            != "All Branches"
        ):

            filtered_history = (
                filtered_history[
                    filtered_history[
                        "branch"
                    ]
                    == selected_branch
                ]
            )

        if (
            selected_year
            != "All Years"
        ):

            filtered_history = (
                filtered_history[
                    filtered_history[
                        "observed_at"
                    ]
                    .dt.year
                    == int(
                        selected_year
                    )
                ]
            )

        if (
            selected_month
            != "All Months"
        ):

            month_number = (
                month_options.index(
                    selected_month
                )
            )

            filtered_history = (
                filtered_history[
                    filtered_history[
                        "observed_at"
                    ]
                    .dt.month
                    == month_number
                ]
            )

    # ========================================================
    # RECRUITMENT OVERVIEW
    # ========================================================

    st.markdown(
        "## 📌 Recruitment Overview"
    )

    company_count = (
        filtered_current[
            "company_name"
        ].nunique()
        if not filtered_current.empty
        else 0
    )

    role_count = (
        filtered_current[
            "job_title"
        ].nunique()
        if not filtered_current.empty
        else 0
    )

    location_count = (
        filtered_current[
            "location"
        ].nunique()
        if not filtered_current.empty
        else 0
    )

    history_unique = (
        filtered_history.apply(
            job_key,
            axis=1,
        ).nunique()
        if not filtered_history.empty
        else 0
    )

    k1, k2, k3, k4, k5 = (
        st.columns(5)
    )

    with k1:

        st.metric(
            "🔴 Current Openings",
            f"{len(filtered_current):,}",
        )

    with k2:

        st.metric(
            "🏢 Companies",
            f"{company_count:,}",
        )

    with k3:

        st.metric(
            "💼 Roles",
            f"{role_count:,}",
        )

    with k4:

        st.metric(
            "📍 Locations",
            f"{location_count:,}",
        )

    with k5:

        st.metric(
            "📚 Historical Jobs",
            f"{history_unique:,}",
        )

    # ========================================================
    # BRANCH DEMAND
    # ========================================================

    st.markdown(
        "## 🎓 Current Branch Demand"
    )

    branch_df = (
        build_branch_intelligence(
            filtered_current
        )
    )

    if branch_df.empty:

        st.info(
            "No ATS openings match the selected filters."
        )

    else:

        branch_col1, branch_col2 = (
            st.columns(2)
        )

        with branch_col1:

            fig = px.bar(
                branch_df,
                x="branch",
                y="openings",
                title="Openings by Branch",
                text="openings",
            )

            fig.update_traces(
                textposition="outside"
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )

        with branch_col2:

            st.dataframe(
                branch_df,
                width="stretch",
                hide_index=True,
            )

    # ========================================================
    # COMPANY INTELLIGENCE
    # ========================================================

    st.markdown(
        "## 🏢 Company Intelligence"
    )

    company_df = (
        build_company_intelligence(
            filtered_current,
            filtered_history,
        )
    )

    if company_df.empty:

        st.info(
            "No company intelligence available."
        )

    else:

        company_col1, company_col2 = (
            st.columns(2)
        )

        with company_col1:

            top_company_chart = (
                company_df.head(10)
            )

            fig = px.bar(
                top_company_chart,
                x="current_openings",
                y="company_name",
                orientation="h",
                title="Top Companies by Current Openings",
                text="current_openings",
            )

            fig.update_layout(
                yaxis={
                    "categoryorder":
                        "total ascending"
                }
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )

        with company_col2:

            display_company = (
                company_df[
                    [
                        "company_name",
                        "current_openings",
                        "current_roles",
                        "current_locations",
                        "historical_jobs",
                        "activity_index",
                    ]
                ].head(15)
            )

            st.dataframe(
                display_company,
                width="stretch",
                hide_index=True,
            )

    st.caption(
        "Activity Index is a descriptive recruitment-activity "
        "measure based on observed current and historical ATS "
        "openings. It is NOT hiring probability."
    )

    # ========================================================
    # ROLE INTELLIGENCE
    # ========================================================

    st.markdown(
        "## 💼 Role Intelligence"
    )

    role_df = (
        build_role_intelligence(
            filtered_current
        )
    )

    if role_df.empty:

        st.info(
            "No role intelligence available."
        )

    else:

        role_col1, role_col2 = (
            st.columns(2)
        )

        with role_col1:

            top_roles = (
                role_df.head(15)
            )

            fig = px.bar(
                top_roles,
                x="openings",
                y="job_title",
                color="branch",
                orientation="h",
                title="Top Current Roles",
            )

            fig.update_layout(
                yaxis={
                    "categoryorder":
                        "total ascending"
                }
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )

        with role_col2:

            st.dataframe(
                role_df.head(20),
                width="stretch",
                hide_index=True,
            )

    # ========================================================
    # LOCATION INTELLIGENCE
    # ========================================================

    st.markdown(
        "## 📍 Location Intelligence"
    )

    location_df = (
        build_location_intelligence(
            filtered_current
        )
    )

    if location_df.empty:

        st.info(
            "No location data available."
        )

    else:

        location_col1, location_col2 = (
            st.columns(2)
        )

        with location_col1:

            fig = px.bar(
                location_df.head(10),
                x="openings",
                y="location",
                orientation="h",
                title="Top Hiring Locations",
                text="openings",
            )

            fig.update_layout(
                yaxis={
                    "categoryorder":
                        "total ascending"
                }
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )

        with location_col2:

            st.dataframe(
                location_df.head(15),
                width="stretch",
                hide_index=True,
            )

    # ========================================================
    # HISTORICAL ATS TREND
    # ========================================================

    st.markdown(
        "## 📈 Historical ATS Opening Trend"
    )

    run_summary = (
        build_collection_run_summary(
            filtered_history
        )
    )

    if run_summary.empty:

        st.info(
            "Historical ATS data is not available yet."
        )

    else:

        fig = px.line(
            run_summary,
            x="run_started",
            y="openings",
            markers=True,
            title="Observed ATS Openings by Collection Run",
        )

        fig.update_yaxes(
            title="Distinct Openings"
        )

        fig.update_xaxes(
            title="Collection Run"
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

        st.dataframe(
            run_summary,
            width="stretch",
            hide_index=True,
        )

    st.caption(
        "Each collection run represents a snapshot of company "
        "career-system openings. Distinct job IDs are used to "
        "avoid double counting within a snapshot."
    )

    # ========================================================
    # MONTHLY RECRUITMENT ACTIVITY
    # ========================================================

    st.markdown(
        "## 📆 Monthly Recruitment Activity"
    )

    monthly_df = (
        build_monthly_activity(
            history_jobs
        )
    )

    if monthly_df.empty:

        st.info(
            "Monthly ATS activity will appear after more "
            "collection runs are accumulated."
        )

    else:

        fig = px.line(
            monthly_df,
            x="month",
            y="openings",
            markers=True,
            title="Monthly Distinct ATS Opening Activity",
        )

        fig.update_yaxes(
            title="Distinct Openings"
        )

        fig.update_xaxes(
            title="Month"
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

        st.dataframe(
            monthly_df,
            width="stretch",
            hide_index=True,
        )

    # ========================================================
    # FUTURE HIRING SIGNAL
    # ========================================================

    st.markdown(
        "## 🔮 Future Hiring Signal"
    )

    if run_summary.empty:

        st.info(
            "Future hiring signals will become meaningful after "
            "multiple ATS collection snapshots are accumulated."
        )

    elif len(run_summary) < 3:

        st.warning(
            "Future hiring prediction is not enabled yet. "
            f"Only {len(run_summary)} ATS collection snapshots "
            "are available. Continue running the collector "
            "regularly to build a reliable time series."
        )

        latest_openings = int(
            run_summary.iloc[-1][
                "openings"
            ]
        )

        previous_openings = int(
            run_summary.iloc[-2][
                "openings"
            ]
        )

        change = (
            latest_openings
            -
            previous_openings
        )

        if change > 0:

            signal = "Increasing"

        elif change < 0:

            signal = "Decreasing"

        else:

            signal = "Stable"

        f1, f2, f3 = (
            st.columns(3)
        )

        with f1:

            st.metric(
                "Latest Openings",
                f"{latest_openings:,}",
            )

        with f2:

            st.metric(
                "Change vs Previous Snapshot",
                f"{change:+,}",
            )

        with f3:

            st.metric(
                "Hiring Momentum",
                signal,
            )

        st.caption(
            "This is an observed momentum signal, not a "
            "statistically trained future-hiring probability."
        )

    else:

        recent = (
            run_summary.tail(3)
        )

        first_value = float(
            recent.iloc[0][
                "openings"
            ]
        )

        latest_value = float(
            recent.iloc[-1][
                "openings"
            ]
        )

        if first_value > 0:

            growth_rate = (
                (
                    latest_value
                    -
                    first_value
                )
                /
                first_value
                * 100
            )

        else:

            growth_rate = 0

        if growth_rate > 5:

            signal = "Increasing"

        elif growth_rate < -5:

            signal = "Decreasing"

        else:

            signal = "Stable"

        f1, f2, f3 = (
            st.columns(3)
        )

        with f1:

            st.metric(
                "Latest Openings",
                f"{int(latest_value):,}",
            )

        with f2:

            st.metric(
                "Recent Growth",
                f"{growth_rate:+.1f}%",
            )

        with f3:

            st.metric(
                "Hiring Momentum",
                signal,
            )

        st.info(
            "The current Future Hiring Signal is based on "
            "observed ATS opening momentum. A trained forecasting "
            "model should be added only after sufficient historical "
            "collection snapshots have been accumulated."
        )

    # ========================================================
    # CURRENT LIVE OPENINGS
    # ========================================================

    st.markdown(
        "## 🔴 Current ATS Openings"
    )

    if filtered_current.empty:

        st.warning(
            "No current live openings match the selected filters."
        )

    else:

        display_columns = [
            "company_name",
            "job_title",
            "branch",
            "location",
            "experience",
            "work_mode",
            "source",
            "status",
            "application_url",
        ]

        available_columns = [
            column
            for column in display_columns
            if column
            in filtered_current.columns
        ]

        display_jobs = (
            filtered_current[
                available_columns
            ].copy()
        )

        st.dataframe(
            display_jobs,
            width="stretch",
            hide_index=True,
            column_config={
                "application_url":
                    st.column_config.LinkColumn(
                        "Apply",
                        display_text="Apply Now",
                    ),
            },
        )

    # ========================================================
    # PAST ATS OPENINGS
    # ========================================================

    st.markdown(
        "## 📚 Past ATS Openings"
    )

    if filtered_history.empty:

        st.info(
            "No historical ATS openings match "
            "the selected filters."
        )

    else:

        past = (
            filtered_history.copy()
        )

        past["_job_key"] = past.apply(
            job_key,
            axis=1,
        )

        # Keep latest observation
        # for each job.

        past = (
            past
            .sort_values(
                "observed_at",
                ascending=False,
            )
            .drop_duplicates(
                subset=["_job_key"],
                keep="first",
            )
        )

        past_display_columns = [
            "company_name",
            "job_title",
            "branch",
            "location",
            "experience",
            "status",
            "observed_at",
            "first_seen_at",
            "last_seen_at",
            "closed_at",
            "source",
            "application_url",
        ]

        available_past_columns = [
            column
            for column
            in past_display_columns
            if column
            in past.columns
        ]

        past_display = (
            past[
                available_past_columns
            ].copy()
        )

        st.dataframe(
            past_display,
            width="stretch",
            hide_index=True,
            column_config={
                "application_url":
                    st.column_config.LinkColumn(
                        "Application",
                        display_text="Open",
                    ),
            },
        )

        st.caption(
            "Past ATS Openings are historical observations "
            "of job postings. They should not be interpreted "
            "as confirmed historical employee hiring counts."
        )

    # ========================================================
    # 97K JOB MARKET INTELLIGENCE
    # ========================================================

    st.markdown(
        "---"
    )

    st.markdown(
        "# 📊 Job Market Intelligence"
    )

    st.info(
        "The 97K job dataset is used only for broader "
        "job-market analytics and ML. It is NOT used "
        "to display live recommended jobs."
    )

    market_raw = (
        load_market_dataset()
    )

    if market_raw.empty:

        st.warning(
            "97K job-market dataset was not found."
        )

        st.caption(
            "Expected filename: "
            "indian-job-market-dataset-2025.xlsx"
        )

    else:

        market_df = (
            prepare_market_dataset(
                market_raw
            )
        )

        # ----------------------------------------------------
        # Dataset KPIs
        # ----------------------------------------------------

        market_companies = (
            market_df[
                "companyName"
            ].nunique()
            if "companyName"
            in market_df.columns
            else 0
        )

        market_titles = (
            market_df[
                "title"
            ].nunique()
            if "title"
            in market_df.columns
            else 0
        )

        market_locations = (
            market_df[
                "location"
            ].nunique()
            if "location"
            in market_df.columns
            else 0
        )

        mk1, mk2, mk3, mk4 = (
            st.columns(4)
        )

        with mk1:

            st.metric(
                "Dataset Records",
                f"{len(market_df):,}",
            )

        with mk2:

            st.metric(
                "Companies",
                f"{market_companies:,}",
            )

        with mk3:

            st.metric(
                "Job Titles",
                f"{market_titles:,}",
            )

        with mk4:

            st.metric(
                "Locations",
                f"{market_locations:,}",
            )

        # ----------------------------------------------------
        # Market Demand
        # ----------------------------------------------------

        market_demand = (
            calculate_market_demand(
                market_df
            )
        )

        if not market_demand.empty:

            st.markdown(
                "## 📈 Job Market Demand by Branch"
            )

            md_col1, md_col2 = (
                st.columns(2)
            )

            with md_col1:

                fig = px.bar(
                    market_demand,
                    x="branch",
                    y="demand_score",
                    color="demand_class",
                    text="demand_score",
                    title="Market Demand Score",
                )

                fig.update_yaxes(
                    range=[0, 100],
                    title="Demand Score",
                )

                st.plotly_chart(
                    fig,
                    width="stretch",
                )

            with md_col2:

                st.dataframe(
                    market_demand,
                    width="stretch",
                    hide_index=True,
                )

            st.caption(
                "Market Demand Score uses posting volume, "
                "unique companies and unique locations. "
                "It is job-market demand, not candidate hiring "
                "probability."
            )

        # ----------------------------------------------------
        # Experience Distribution
        # ----------------------------------------------------

        if (
            "experience_midpoint"
            in market_df.columns
        ):

            experience_market = (
                market_df[
                    "experience_midpoint"
                ]
                .dropna()
            )

            if not experience_market.empty:

                st.markdown(
                    "## 👨‍💻 Experience Distribution"
                )

                fig = px.histogram(
                    experience_market,
                    x="experience_midpoint",
                    nbins=15,
                    title="Job Experience Distribution",
                )

                fig.update_xaxes(
                    title="Experience"
                )

                fig.update_yaxes(
                    title="Job Count"
                )

                st.plotly_chart(
                    fig,
                    width="stretch",
                )

    # ========================================================
    # XGBOOST ML PREDICTION
    # ========================================================

    st.markdown(
        "---"
    )

    st.markdown(
        "# 🤖 Machine Learning Demand Prediction"
    )

    st.info(
        "This model predicts job-market demand class. "
        "It does NOT predict whether a particular student "
        "will be hired."
    )

    with st.expander(
        "Open XGBoost Demand Prediction"
    ):

        ml_col1, ml_col2 = (
            st.columns(2)
        )

        with ml_col1:

            minimum_experience = (
                st.number_input(
                    "Minimum Experience",
                    min_value=0.0,
                    max_value=30.0,
                    value=0.0,
                    step=1.0,
                )
            )

            maximum_experience = (
                st.number_input(
                    "Maximum Experience",
                    min_value=0.0,
                    max_value=40.0,
                    value=3.0,
                    step=1.0,
                )
            )

            salary_midpoint = (
                st.number_input(
                    "Salary Midpoint",
                    min_value=0.0,
                    value=0.0,
                    step=1000.0,
                )
            )

            experience_midpoint = (
                st.number_input(
                    "Experience Midpoint",
                    min_value=0.0,
                    max_value=40.0,
                    value=1.5,
                    step=0.5,
                )
            )

            salary_range = (
                st.number_input(
                    "Salary Range",
                    min_value=0.0,
                    value=0.0,
                    step=1000.0,
                )
            )

        with ml_col2:

            experience_range = (
                st.number_input(
                    "Experience Range",
                    min_value=0.0,
                    max_value=40.0,
                    value=3.0,
                    step=1.0,
                )
            )

            skill_count = (
                st.number_input(
                    "Skill Count",
                    min_value=0,
                    max_value=100,
                    value=5,
                    step=1,
                )
            )

            is_remote = (
                st.selectbox(
                    "Remote Job",
                    [
                        0,
                        1,
                    ],
                )
            )

            title_length = (
                st.number_input(
                    "Title Length",
                    min_value=1,
                    max_value=500,
                    value=30,
                    step=1,
                )
            )

            company_name_length = (
                st.number_input(
                    "Company Name Length",
                    min_value=1,
                    max_value=300,
                    value=15,
                    step=1,
                )
            )

        if st.button(
            "🚀 Predict Job-Market Demand",
            type="primary",
        ):

            payload = {
                "minimum_experience":
                    minimum_experience,

                "maximum_experience":
                    maximum_experience,

                "salary_midpoint":
                    salary_midpoint,

                "experience_midpoint":
                    experience_midpoint,

                "salary_range":
                    salary_range,

                "experience_range":
                    experience_range,

                "skill_count":
                    skill_count,

                "is_remote":
                    int(is_remote),

                "title_length":
                    title_length,

                "company_name_length":
                    company_name_length,
            }

            result = (
                request_ml_prediction(
                    payload
                )
            )

            if "error" in result:

                st.error(
                    "ML API request failed: "
                    + str(
                        result["error"]
                    )
                )

            else:

                demand_class = (
                    result.get(
                        "demand_class",
                        "Unknown",
                    )
                )

                probability = (
                    result.get(
                        "probability"
                    )
                )

                st.success(
                    f"Prediction: {demand_class}"
                )

                ml1, ml2 = (
                    st.columns(2)
                )

                with ml1:

                    st.metric(
                        "Demand Class",
                        demand_class,
                    )

                with ml2:

                    if probability is not None:

                        st.metric(
                            "High-Demand Probability",
                            f"{float(probability) * 100:.2f}%",
                        )

                st.caption(
                    "Probability shown here is the model's "
                    "probability of the high job-market-demand "
                    "class. It is NOT hiring probability."
                )

    # ========================================================
    # FOOTER
    # ========================================================

    st.markdown(
        "---"
    )

    st.success(
        "Recruitment Intelligence is connected to the "
        "ATS-backed recruitment data pipeline."
    )

    st.caption(
        "Architecture: Company ATS → Live Job Collector → "
        "PostgreSQL → Recruitment Intelligence → "
        "ML / Analytics"
    )


# ============================================================
# DIRECT EXECUTION SUPPORT
# ============================================================

if __name__ == "__main__":

    show_recruitment_intelligence()