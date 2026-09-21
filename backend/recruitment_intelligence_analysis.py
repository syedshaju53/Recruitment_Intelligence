

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from urllib.parse import quote_plus


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_NAME = os.environ.get("POSTGRES_DB", "recruitment_db")


if not DB_PASSWORD:
    raise RuntimeError(
        "POSTGRES_PASSWORD is not set.\n"
        "Set your PostgreSQL password in the terminal before running "
        "Recruitment Intelligence."
    )


DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{quote_plus(DB_PASSWORD)}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


engine: Engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# ============================================================
# TARGET BRANCHES
# ============================================================

BRANCH_KEYWORDS = {
    "cse": [
        "computer science",
        "computer engineering",
        "software",
        "developer",
        "development",
        "data",
        "machine learning",
        "artificial intelligence",
        "ai engineer",
        "ml engineer",
        "cloud",
        "devops",
        "cyber security",
        "cybersecurity",
        "database",
        "backend",
        "frontend",
        "full stack",
        "fullstack",
        "web developer",
        "python developer",
        "java developer",
        "qa engineer",
        "test engineer",
        "automation engineer",
        "network engineer",
        "application engineer",
        "systems engineer",
    ],

    "ece": [
        "electronics",
        "electronic",
        "embedded",
        "firmware",
        "vlsi",
        "verilog",
        "asic",
        "fpga",
        "hardware engineer",
        "hardware",
        "iot",
        "internet of things",
        "semiconductor",
        "pcb",
        "telecom",
        "telecommunication",
        "rf engineer",
        "radio frequency",
        "electrical and electronics",
    ],

    "civil": [
        "civil engineer",
        "civil engineering",
        "structural engineer",
        "structural engineering",
        "site engineer",
        "construction",
        "quantity surveyor",
        "quantity surveying",
        "bim",
        "autocad",
        "civil design",
        "project engineer",
        "planning engineer",
        "building engineer",
        "infrastructure engineer",
        "highway engineer",
        "road engineer",
    ],

    "mechanical": [
        "mechanical engineer",
        "mechanical engineering",
        "mechanical design",
        "cad engineer",
        "design engineer",
        "manufacturing",
        "production engineer",
        "maintenance engineer",
        "automotive",
        "automobile",
        "hvac",
        "process engineer",
        "industrial engineer",
        "quality engineer",
        "tool design",
        "solidworks",
        "catia",
        "creo",
    ],
}


# ============================================================
# EXCLUDED JOB TYPES
# ============================================================

ACADEMIC_KEYWORDS = [
    "lecturer",
    "professor",
    "assistant professor",
    "associate professor",
    "teacher",
    "teaching",
    "faculty",
    "academic",
    "trainer",
    "training instructor",
    "school teacher",
    "college teacher",
    "education",
    "education consultant",
    "tutor",
    "instructor",
    "principal",
]


NON_TECHNICAL_KEYWORDS = [
    "sales",
    "sales executive",
    "sales manager",
    "marketing",
    "marketing executive",
    "business development",
    "business development executive",
    "hr",
    "human resources",
    "recruiter",
    "recruitment",
    "talent acquisition",
    "finance",
    "financial advisor",
    "accountant",
    "accounting",
    "banking sales",
    "insurance sales",
    "telecaller",
    "telecalling",
    "customer service",
    "customer support",
    "operations executive",
    "relationship manager",
    "content writer",
    "copywriter",
    "legal",
    "lawyer",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_text(value) -> str:
    """
    Safely convert database values into searchable text.
    """

    if value is None:
        return ""

    if isinstance(value, (list, tuple, set)):
        return " ".join(clean_text(v) for v in value)

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip().lower()


def title_text(row: pd.Series) -> str:
    return clean_text(
        row.get("job_title", "")
    )


def combined_job_text(row: pd.Series) -> str:
    """
    Combine important ATS fields for branch classification.
    """

    fields = [
        row.get("job_title", ""),
        row.get("department", ""),
        row.get("skills", ""),
        row.get("job_description", ""),
        row.get("company_name", ""),
    ]

    return " ".join(clean_text(x) for x in fields)


def is_academic_job(row: pd.Series) -> bool:
    """
    Remove teaching / academic jobs.
    """

    title = clean_text(row.get("job_title", ""))

    return any(
        keyword in title
        for keyword in ACADEMIC_KEYWORDS
    )


def is_non_technical_job(row: pd.Series) -> bool:
    """
    Remove non-technical company roles.
    """

    title = clean_text(row.get("job_title", ""))

    return any(
        keyword in title
        for keyword in NON_TECHNICAL_KEYWORDS
    )


def detect_branch(row: pd.Series) -> str:
    """
    Detect the most relevant engineering branch.

    Priority is based on title first, then combined job text.
    """

    title = clean_text(row.get("job_title", ""))

    # --------------------------------------------------------
    # TITLE FIRST
    # --------------------------------------------------------

    for branch, keywords in BRANCH_KEYWORDS.items():

        for keyword in keywords:

            if keyword in title:
                return branch

    # --------------------------------------------------------
    # FULL JOB TEXT
    # --------------------------------------------------------

    combined = combined_job_text(row)

    scores = {}

    for branch, keywords in BRANCH_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            if keyword in combined:
                score += 1

        scores[branch] = score

    if not scores:
        return "other"

    best_branch = max(
        scores,
        key=scores.get,
    )

    if scores[best_branch] == 0:
        return "other"

    return best_branch


def is_target_job(row: pd.Series) -> bool:
    """
    True only for:
        CSE
        ECE
        Civil
        Mechanical

    and excludes:
        teaching
        academic
        non-technical jobs
    """

    if is_academic_job(row):
        return False

    if is_non_technical_job(row):
        return False

    branch = detect_branch(row)

    return branch in {
        "cse",
        "ece",
        "civil",
        "mechanical",
    }


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and classify ATS job data.
    """

    if df.empty:
        return df

    df = df.copy()

    # --------------------------------------------------------
    # STANDARDIZE COLUMN NAMES
    # --------------------------------------------------------

    df.columns = [
        str(column).strip().lower()
        for column in df.columns
    ]

    # --------------------------------------------------------
    # REQUIRED COLUMNS
    # --------------------------------------------------------

    required_columns = [
        "job_id",
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
        "source_job_id",
        "status",
        "observed_at",
        "first_seen_at",
        "last_seen_at",
        "closed_at",
        "collection_run_id",
    ]

    for column in required_columns:

        if column not in df.columns:
            df[column] = None

    # --------------------------------------------------------
    # DATETIME
    # --------------------------------------------------------

    for column in [
        "observed_at",
        "first_seen_at",
        "last_seen_at",
        "closed_at",
    ]:

        df[column] = pd.to_datetime(
            df[column],
            errors="coerce",
        )

    # --------------------------------------------------------
    # BRANCH
    # --------------------------------------------------------

    df["branch"] = df.apply(
        detect_branch,
        axis=1,
    )

    # --------------------------------------------------------
    # FILTER TARGET JOBS
    # --------------------------------------------------------

    df["is_academic"] = df.apply(
        is_academic_job,
        axis=1,
    )

    df["is_non_technical"] = df.apply(
        is_non_technical_job,
        axis=1,
    )

    df = df[
        (
            ~df["is_academic"]
        )
        &
        (
            ~df["is_non_technical"]
        )
        &
        (
            df["branch"].isin(
                [
                    "cse",
                    "ece",
                    "civil",
                    "mechanical",
                ]
            )
        )
    ].copy()

    return df


# ============================================================
# DATABASE LOADING
# ============================================================

def load_live_jobs() -> pd.DataFrame:
    """
    Load currently open jobs from live_jobs.
    """

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
        WHERE LOWER(COALESCE(status, '')) = 'open'
        ORDER BY last_checked DESC NULLS LAST;
        """
    )

    with engine.connect() as connection:

        df = pd.read_sql(
            query,
            connection,
        )

    if df.empty:
        return df

    df["observed_at"] = df["last_checked"]

    return prepare_dataframe(df)


def load_job_history() -> pd.DataFrame:
    """
    Load historical ATS observations.

    Every collection_run_id represents one execution
    of the ATS collector.
    """

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
        ORDER BY observed_at ASC;
        """
    )

    with engine.connect() as connection:

        df = pd.read_sql(
            query,
            connection,
        )

    if df.empty:
        return df

    return prepare_dataframe(df)


# ============================================================
# COLLECTION RUN ANALYSIS
# ============================================================

def get_collection_runs(
    history_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Return one row per ATS collection run.
    """

    if history_df is None:
        history_df = load_job_history()

    if history_df.empty:
        return pd.DataFrame(
            columns=[
                "collection_run_id",
                "run_started",
                "run_ended",
                "total_observations",
                "unique_jobs",
                "unique_companies",
            ]
        )

    runs = (
        history_df
        .groupby("collection_run_id", dropna=False)
        .agg(
            run_started=("observed_at", "min"),
            run_ended=("observed_at", "max"),
            total_observations=("id", "count"),
            unique_jobs=("job_id", "nunique"),
            unique_companies=("company_name", "nunique"),
        )
        .reset_index()
        .sort_values("run_started")
    )

    return runs


# ============================================================
# CURRENT OPENINGS
# ============================================================

def current_openings_summary(
    live_df: Optional[pd.DataFrame] = None,
) -> dict:
    """
    Summary of currently open ATS jobs.
    """

    if live_df is None:
        live_df = load_live_jobs()

    if live_df.empty:
        return {
            "total_openings": 0,
            "companies": 0,
            "roles": 0,
            "locations": 0,
        }

    return {
        "total_openings": int(
            live_df["job_id"].nunique()
        ),
        "companies": int(
            live_df["company_name"].nunique()
        ),
        "roles": int(
            live_df["job_title"].nunique()
        ),
        "locations": int(
            live_df["location"].nunique()
        ),
    }


# ============================================================
# CURRENT OPENINGS BY BRANCH
# ============================================================

def current_branch_demand(
    live_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:

    if live_df is None:
        live_df = load_live_jobs()

    if live_df.empty:
        return pd.DataFrame(
            columns=[
                "branch",
                "openings",
                "companies",
            ]
        )

    result = (
        live_df
        .groupby("branch")
        .agg(
            openings=("job_id", "nunique"),
            companies=("company_name", "nunique"),
        )
        .reset_index()
        .sort_values(
            "openings",
            ascending=False,
        )
    )

    return result


# ============================================================
# CURRENT OPENINGS BY COMPANY
# ============================================================

def current_company_demand(
    live_df: Optional[pd.DataFrame] = None,
    top_n: int = 20,
) -> pd.DataFrame:

    if live_df is None:
        live_df = load_live_jobs()

    if live_df.empty:
        return pd.DataFrame(
            columns=[
                "company_name",
                "openings",
                "roles",
                "locations",
            ]
        )

    result = (
        live_df
        .groupby("company_name")
        .agg(
            openings=("job_id", "nunique"),
            roles=("job_title", "nunique"),
            locations=("location", "nunique"),
        )
        .reset_index()
        .sort_values(
            "openings",
            ascending=False,
        )
        .head(top_n)
    )

    return result


# ============================================================
# CURRENT OPENINGS BY ROLE
# ============================================================

def current_role_demand(
    live_df: Optional[pd.DataFrame] = None,
    top_n: int = 20,
) -> pd.DataFrame:

    if live_df is None:
        live_df = load_live_jobs()

    if live_df.empty:
        return pd.DataFrame(
            columns=[
                "job_title",
                "openings",
                "companies",
            ]
        )

    result = (
        live_df
        .groupby("job_title")
        .agg(
            openings=("job_id", "nunique"),
            companies=("company_name", "nunique"),
        )
        .reset_index()
        .sort_values(
            "openings",
            ascending=False,
        )
        .head(top_n)
    )

    return result


# ============================================================
# CURRENT OPENINGS BY LOCATION
# ============================================================

def current_location_demand(
    live_df: Optional[pd.DataFrame] = None,
    top_n: int = 20,
) -> pd.DataFrame:

    if live_df is None:
        live_df = load_live_jobs()

    if live_df.empty:
        return pd.DataFrame(
            columns=[
                "location",
                "openings",
                "companies",
            ]
        )

    result = (
        live_df
        .groupby("location")
        .agg(
            openings=("job_id", "nunique"),
            companies=("company_name", "nunique"),
        )
        .reset_index()
        .sort_values(
            "openings",
            ascending=False,
        )
        .head(top_n)
    )

    return result


# ============================================================
# HISTORICAL OPENING TREND
# ============================================================

def historical_opening_trend(
    history_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Count unique jobs observed in each ATS collection run.

    Important:
        We count DISTINCT job_id instead of raw rows so that
        multiple records for the same job don't artificially
        inflate the trend.
    """

    if history_df is None:
        history_df = load_job_history()

    if history_df.empty:
        return pd.DataFrame(
            columns=[
                "collection_run_id",
                "run_started",
                "openings",
                "companies",
            ]
        )

    result = (
        history_df
        .groupby("collection_run_id")
        .agg(
            run_started=("observed_at", "min"),
            openings=("job_id", "nunique"),
            companies=("company_name", "nunique"),
        )
        .reset_index()
        .sort_values("run_started")
    )

    return result


# ============================================================
# HISTORICAL BRANCH TREND
# ============================================================

def historical_branch_trend(
    history_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:

    if history_df is None:
        history_df = load_job_history()

    if history_df.empty:
        return pd.DataFrame()

    result = (
        history_df
        .groupby(
            [
                "collection_run_id",
                "branch",
            ]
        )
        .agg(
            run_started=("observed_at", "min"),
            openings=("job_id", "nunique"),
            companies=("company_name", "nunique"),
        )
        .reset_index()
        .sort_values("run_started")
    )

    return result


# ============================================================
# MONTHLY HISTORICAL ACTIVITY
# ============================================================

def monthly_recruitment_activity(
    history_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Monthly ATS activity.

    This becomes more meaningful as the collector runs over
    multiple days/weeks/months.
    """

    if history_df is None:
        history_df = load_job_history()

    if history_df.empty:
        return pd.DataFrame(
            columns=[
                "month",
                "openings",
                "companies",
                "roles",
            ]
        )

    df = history_df.copy()

    df["month"] = (
        df["observed_at"]
        .dt.to_period("M")
        .astype(str)
    )

    result = (
        df
        .groupby("month")
        .agg(
            openings=("job_id", "nunique"),
            companies=("company_name", "nunique"),
            roles=("job_title", "nunique"),
        )
        .reset_index()
        .sort_values("month")
    )

    return result


# ============================================================
# MONTHLY BRANCH ACTIVITY
# ============================================================

def monthly_branch_activity(
    history_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:

    if history_df is None:
        history_df = load_job_history()

    if history_df.empty:
        return pd.DataFrame()

    df = history_df.copy()

    df["month"] = (
        df["observed_at"]
        .dt.to_period("M")
        .astype(str)
    )

    result = (
        df
        .groupby(
            [
                "month",
                "branch",
            ]
        )
        .agg(
            openings=("job_id", "nunique"),
            companies=("company_name", "nunique"),
        )
        .reset_index()
        .sort_values("month")
    )

    return result


# ============================================================
# OPEN VS CLOSED ANALYSIS
# ============================================================

def opening_status_summary(
    history_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:

    if history_df is None:
        history_df = load_job_history()

    if history_df.empty:
        return pd.DataFrame(
            columns=[
                "status",
                "jobs",
            ]
        )

    result = (
        history_df
        .groupby("status")
        .agg(
            jobs=("job_id", "nunique")
        )
        .reset_index()
        .sort_values(
            "jobs",
            ascending=False,
        )
    )

    return result


# ============================================================
# COMPANY HISTORICAL ACTIVITY
# ============================================================

def company_historical_activity(
    history_df: Optional[pd.DataFrame] = None,
    top_n: int = 20,
) -> pd.DataFrame:

    if history_df is None:
        history_df = load_job_history()

    if history_df.empty:
        return pd.DataFrame()

    result = (
        history_df
        .groupby("company_name")
        .agg(
            observed_openings=("job_id", "nunique"),
            roles=("job_title", "nunique"),
            locations=("location", "nunique"),
            first_observed=("observed_at", "min"),
            last_observed=("observed_at", "max"),
        )
        .reset_index()
        .sort_values(
            "observed_openings",
            ascending=False,
        )
        .head(top_n)
    )

    return result


# ============================================================
# ROLE HISTORICAL ACTIVITY
# ============================================================

def role_historical_activity(
    history_df: Optional[pd.DataFrame] = None,
    top_n: int = 20,
) -> pd.DataFrame:

    if history_df is None:
        history_df = load_job_history()

    if history_df.empty:
        return pd.DataFrame()

    result = (
        history_df
        .groupby("job_title")
        .agg(
            observed_openings=("job_id", "nunique"),
            companies=("company_name", "nunique"),
            locations=("location", "nunique"),
        )
        .reset_index()
        .sort_values(
            "observed_openings",
            ascending=False,
        )
        .head(top_n)
    )

    return result


# ============================================================
# LOCATION HISTORICAL ACTIVITY
# ============================================================

def location_historical_activity(
    history_df: Optional[pd.DataFrame] = None,
    top_n: int = 20,
) -> pd.DataFrame:

    if history_df is None:
        history_df = load_job_history()

    if history_df.empty:
        return pd.DataFrame()

    result = (
        history_df
        .groupby("location")
        .agg(
            observed_openings=("job_id", "nunique"),
            companies=("company_name", "nunique"),
            roles=("job_title", "nunique"),
        )
        .reset_index()
        .sort_values(
            "observed_openings",
            ascending=False,
        )
        .head(top_n)
    )

    return result


# ============================================================
# EXPERIENCE ANALYSIS
# ============================================================

def extract_experience_number(value) -> Optional[float]:
    """
    Extract a numeric experience value.

    Examples:

        '0-2 years' -> 0
        '2-5 years' -> 2
        '5 years'   -> 5
    """

    value = clean_text(value)

    if not value:
        return None

    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        value,
    )

    if not numbers:
        return None

    try:
        return float(numbers[0])
    except Exception:
        return None


def experience_distribution(
    live_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:

    if live_df is None:
        live_df = load_live_jobs()

    if live_df.empty:
        return pd.DataFrame()

    df = live_df.copy()

    df["experience_years"] = df[
        "experience"
    ].apply(
        extract_experience_number
    )

    df = df[
        df["experience_years"].notna()
    ].copy()

    if df.empty:
        return pd.DataFrame()

    result = (
        df
        .groupby("experience_years")
        .agg(
            openings=("job_id", "nunique")
        )
        .reset_index()
        .sort_values("experience_years")
    )

    return result


# ============================================================
# SALARY ANALYSIS
# ============================================================

def extract_salary_number(value) -> Optional[float]:
    """
    Extract first numeric salary value from a salary string.

    Currency is deliberately NOT assumed.
    """

    value = clean_text(value)

    if not value:
        return None

    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        value.replace(",", ""),
    )

    if not numbers:
        return None

    try:
        number = float(numbers[0])

        if number <= 0:
            return None

        return number

    except Exception:
        return None


def salary_summary(
    live_df: Optional[pd.DataFrame] = None,
) -> dict:

    if live_df is None:
        live_df = load_live_jobs()

    if live_df.empty:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "minimum": None,
            "maximum": None,
        }

    df = live_df.copy()

    df["salary_value"] = df[
        "salary"
    ].apply(
        extract_salary_number
    )

    salary = df[
        "salary_value"
    ].dropna()

    if salary.empty:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "minimum": None,
            "maximum": None,
        }

    return {
        "count": int(salary.count()),
        "mean": float(salary.mean()),
        "median": float(salary.median()),
        "minimum": float(salary.min()),
        "maximum": float(salary.max()),
    }


# ============================================================
# JOB LIFECYCLE
# ============================================================

def job_lifecycle_analysis(
    history_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Determine how long jobs have been observed by ATS.

    This helps distinguish:

        newly observed
        repeatedly observed
        potentially closed
    """

    if history_df is None:
        history_df = load_job_history()

    if history_df.empty:
        return pd.DataFrame()

    grouped = (
        history_df
        .groupby(
            [
                "job_id",
                "company_name",
                "job_title",
            ]
        )
        .agg(
            first_observed=("observed_at", "min"),
            last_observed=("observed_at", "max"),
            observations=("collection_run_id", "nunique"),
            statuses=("status", "nunique"),
        )
        .reset_index()
    )

    grouped["duration_days"] = (
        grouped["last_observed"]
        - grouped["first_observed"]
    ).dt.total_seconds() / 86400

    grouped["duration_days"] = (
        grouped["duration_days"]
        .round(2)
    )

    return grouped.sort_values(
        "observations",
        ascending=False,
    )


# ============================================================
# NEW / REPEATED / CLOSED JOB ANALYSIS
# ============================================================

def job_lifecycle_summary(
    history_df: Optional[pd.DataFrame] = None,
) -> dict:

    lifecycle = job_lifecycle_analysis(
        history_df
    )

    if lifecycle.empty:
        return {
            "unique_jobs": 0,
            "repeated_jobs": 0,
            "single_observation_jobs": 0,
        }

    return {
        "unique_jobs": int(
            lifecycle["job_id"].nunique()
        ),
        "repeated_jobs": int(
            (
                lifecycle["observations"] > 1
            ).sum()
        ),
        "single_observation_jobs": int(
            (
                lifecycle["observations"] == 1
            ).sum()
        ),
    }


# ============================================================
# ATS DATASET SUMMARY
# ============================================================

def generate_summary() -> dict:
    """
    Generate complete ATS recruitment summary.
    """

    live_df = load_live_jobs()
    history_df = load_job_history()

    current = current_openings_summary(
        live_df
    )

    runs = get_collection_runs(
        history_df
    )

    lifecycle = job_lifecycle_summary(
        history_df
    )

    return {
        "current_openings": current,
        "historical_unique_jobs": int(
            history_df["job_id"].nunique()
        )
        if not history_df.empty
        else 0,
        "historical_companies": int(
            history_df["company_name"].nunique()
        )
        if not history_df.empty
        else 0,
        "historical_roles": int(
            history_df["job_title"].nunique()
        )
        if not history_df.empty
        else 0,
        "collection_runs": int(
            runs["collection_run_id"].nunique()
        )
        if not runs.empty
        else 0,
        "repeated_jobs": lifecycle[
            "repeated_jobs"
        ],
        "single_observation_jobs": lifecycle[
            "single_observation_jobs"
        ],
    }


# ============================================================
# FULL ATS REPORT
# ============================================================

def generate_report() -> dict:
    """
    Generate all major Recruitment Intelligence outputs.
    """

    live_df = load_live_jobs()
    history_df = load_job_history()

    report = {
        "summary": generate_summary(),

        "current_branch_demand":
            current_branch_demand(
                live_df
            ),

        "current_company_demand":
            current_company_demand(
                live_df
            ),

        "current_role_demand":
            current_role_demand(
                live_df
            ),

        "current_location_demand":
            current_location_demand(
                live_df
            ),

        "historical_opening_trend":
            historical_opening_trend(
                history_df
            ),

        "historical_branch_trend":
            historical_branch_trend(
                history_df
            ),

        "monthly_recruitment_activity":
            monthly_recruitment_activity(
                history_df
            ),

        "monthly_branch_activity":
            monthly_branch_activity(
                history_df
            ),

        "company_historical_activity":
            company_historical_activity(
                history_df
            ),

        "role_historical_activity":
            role_historical_activity(
                history_df
            ),

        "location_historical_activity":
            location_historical_activity(
                history_df
            ),

        "opening_status_summary":
            opening_status_summary(
                history_df
            ),

        "experience_distribution":
            experience_distribution(
                live_df
            ),

        "salary_summary":
            salary_summary(
                live_df
            ),

        "job_lifecycle":
            job_lifecycle_analysis(
                history_df
            ),
    }

    return report


# ============================================================
# COMMAND LINE REPORT
# ============================================================

def print_report():
    """
    Print Recruitment Intelligence report.
    """

    print()
    print("=" * 70)
    print("ATS RECRUITMENT INTELLIGENCE")
    print("=" * 70)

    live_df = load_live_jobs()
    history_df = load_job_history()

    # --------------------------------------------------------
    # CURRENT
    # --------------------------------------------------------

    print()
    print("CURRENT OPENINGS")
    print("-" * 70)

    current = current_openings_summary(
        live_df
    )

    print(
        f"Openings   : {current['total_openings']}"
    )

    print(
        f"Companies  : {current['companies']}"
    )

    print(
        f"Roles      : {current['roles']}"
    )

    print(
        f"Locations  : {current['locations']}"
    )

    # --------------------------------------------------------
    # BRANCH
    # --------------------------------------------------------

    print()
    print("CURRENT BRANCH DEMAND")
    print("-" * 70)

    branch_df = current_branch_demand(
        live_df
    )

    if branch_df.empty:
        print("No data.")

    else:
        print(
            branch_df.to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # TOP COMPANIES
    # --------------------------------------------------------

    print()
    print("TOP COMPANIES")
    print("-" * 70)

    company_df = current_company_demand(
        live_df,
        top_n=20,
    )

    if company_df.empty:
        print("No data.")

    else:
        print(
            company_df.to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # TOP ROLES
    # --------------------------------------------------------

    print()
    print("TOP ROLES")
    print("-" * 70)

    role_df = current_role_demand(
        live_df,
        top_n=20,
    )

    if role_df.empty:
        print("No data.")

    else:
        print(
            role_df.to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # LOCATIONS
    # --------------------------------------------------------

    print()
    print("TOP LOCATIONS")
    print("-" * 70)

    location_df = current_location_demand(
        live_df,
        top_n=20,
    )

    if location_df.empty:
        print("No data.")

    else:
        print(
            location_df.to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # COLLECTION RUNS
    # --------------------------------------------------------

    print()
    print("ATS COLLECTION RUNS")
    print("-" * 70)

    runs_df = get_collection_runs(
        history_df
    )

    if runs_df.empty:
        print("No collection history.")

    else:
        print(
            runs_df.to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # HISTORICAL TREND
    # --------------------------------------------------------

    print()
    print("HISTORICAL ATS OPENING TREND")
    print("-" * 70)

    trend_df = historical_opening_trend(
        history_df
    )

    if trend_df.empty:
        print("No historical data.")

    else:
        print(
            trend_df.to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # MONTHLY ACTIVITY
    # --------------------------------------------------------

    print()
    print("MONTHLY RECRUITMENT ACTIVITY")
    print("-" * 70)

    monthly_df = monthly_recruitment_activity(
        history_df
    )

    if monthly_df.empty:
        print("No monthly data.")

    else:
        print(
            monthly_df.to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    print()
    print("OPENING STATUS")
    print("-" * 70)

    status_df = opening_status_summary(
        history_df
    )

    if status_df.empty:
        print("No status data.")

    else:
        print(
            status_df.to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # SALARY
    # --------------------------------------------------------

    print()
    print("SALARY INTELLIGENCE")
    print("-" * 70)

    salary = salary_summary(
        live_df
    )

    print(
        f"Records : {salary['count']}"
    )

    print(
        f"Mean    : {salary['mean']}"
    )

    print(
        f"Median  : {salary['median']}"
    )

    print(
        f"Minimum : {salary['minimum']}"
    )

    print(
        f"Maximum : {salary['maximum']}"
    )

    # --------------------------------------------------------
    # LIFECYCLE
    # --------------------------------------------------------

    print()
    print("JOB LIFECYCLE")
    print("-" * 70)

    lifecycle = job_lifecycle_summary(
        history_df
    )

    print(
        f"Unique jobs              : "
        f"{lifecycle['unique_jobs']}"
    )

    print(
        f"Repeatedly observed jobs : "
        f"{lifecycle['repeated_jobs']}"
    )

    print(
        f"Single-observation jobs  : "
        f"{lifecycle['single_observation_jobs']}"
    )

    print()
    print("=" * 70)
    print("REPORT COMPLETE")
    print("=" * 70)
    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print_report()