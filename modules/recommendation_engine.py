from pathlib import Path
import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REFERENCE_FILE = DATA_DIR / "indian-job-market-dataset-2025.xlsx"


def _normalize_columns(df):
    df.columns = (
        df.columns.astype(str).str.strip().str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )
    return df


def _text(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return str(value).strip()


def _parse_experience(value):
    text = _text(value)
    nums = re.findall(r"\d+(?:\.\d+)?", text)
    if not nums:
        return None, None
    values = [float(x) for x in nums[:2]]
    if len(values) == 1:
        return values[0], values[0]
    return min(values), max(values)


@st.cache_data(show_spinner=False)
def load_reference_jobs():
    if not REFERENCE_FILE.exists():
        raise FileNotFoundError(
            f"97K reference dataset not found: {REFERENCE_FILE}"
        )

    df = pd.read_excel(REFERENCE_FILE)
    df = _normalize_columns(df)

    rename = {
        "jobid": "job_id",
        "companyname": "company_name",
        "tagsandskills": "skills",
        "minimumsalary": "minimum_salary",
        "maximumsalary": "maximum_salary",
        "minimumexperience": "minimum_experience",
        "maximumexperience": "maximum_experience",
        "jobdescription": "job_description",
        "aggregate_rating": "aggregate_rating",
        "reviews_count": "reviews_count",
    }
    df = df.rename(columns=rename)

    for col in [
        "job_id", "title", "company_name", "skills", "experience",
        "salary", "location", "job_description", "currency",
        "job_uploaded", "minimum_salary", "maximum_salary",
        "minimum_experience", "maximum_experience"
    ]:
        if col not in df.columns:
            df[col] = ""

    for col in [
        "title", "company_name", "skills", "experience", "salary",
        "location", "job_description", "currency", "job_uploaded"
    ]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    for col in [
        "minimum_salary", "maximum_salary",
        "minimum_experience", "maximum_experience"
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Some rows may have experience only in the text field.
    missing_min = df["minimum_experience"].isna()

    if missing_min.any():

        parsed = (
            df.loc[missing_min, "experience"]
            .apply(_parse_experience)
        )

        parsed_min = pd.to_numeric(
            [x[0] for x in parsed],
            errors="coerce"
        )

        parsed_max = pd.to_numeric(
            [x[1] for x in parsed],
            errors="coerce"
        )

        df.loc[
            missing_min,
            "minimum_experience"
        ] = parsed_min

        df.loc[
            missing_min,
            "maximum_experience"
        ] = parsed_max

        # Keep a compact corpus for recommendation.
        df["recommendation_text"] = (
            df["title"] + " " +
            df["skills"] + " " +
            df["experience"] + " " +
            df["location"] + " " +
            df["job_description"].str.slice(0, 2500)
        ).str.lower()

        df = df.drop_duplicates(subset=["job_id"], keep="first")
        df = df.reset_index(drop=True)

        return df

    df["minimum_experience"] = pd.to_numeric(
        df["minimum_experience"],
        errors="coerce"
    )

    df["maximum_experience"] = pd.to_numeric(
        df["maximum_experience"],
        errors="coerce"
    )

@st.cache_resource(show_spinner=False)
def build_recommendation_index():
    df = load_reference_jobs()

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
        max_features=15000,
        sublinear_tf=True
    )

    matrix = vectorizer.fit_transform(
        df["recommendation_text"]
    )

    return df, vectorizer, matrix


def _profile_text(profile):
    skills = profile.get("skills", [])
    if isinstance(skills, list):
        skills_text = " ".join(
            str(x) for x in skills
        )
    else:
        skills_text = _text(skills)

    projects = profile.get("projects", [])
    if isinstance(projects, list):
        project_text = " ".join(
            str(x) for x in projects
        )
    else:
        project_text = _text(projects)

    experience = profile.get("experience", [])
    if isinstance(experience, list):
        experience_text = " ".join(
            str(x) for x in experience
        )
    else:
        experience_text = _text(experience)

    return " ".join([
        _text(profile.get("department")),
        _text(profile.get("degree")),
        _text(profile.get("headline")),
        _text(profile.get("about")),
        skills_text,
        project_text,
        experience_text,
    ]).lower().strip()


def recommend_jobs(profile, top_n=10, preferred_location=None):
    df, vectorizer, matrix = build_recommendation_index()

    query = _profile_text(profile)

    if not query:
        # No profile information: return a useful market sample.
        return df.head(top_n).copy()

    query_vector = vectorizer.transform([query])
    similarity = cosine_similarity(
        query_vector, matrix
    ).ravel()

    result = df.copy()
    result["match_score"] = similarity * 100

    # Small deterministic boosts for explicit profile preferences.
    department = _text(profile.get("department")).lower()
    location = _text(
        preferred_location or profile.get("location")
    ).lower()

    if department:
        department_match = (
            result["title"].str.lower().str.contains(
                re.escape(department), na=False
            )
            |
            result["skills"].str.lower().str.contains(
                re.escape(department), na=False
            )
            |
            result["job_description"].str.lower().str.contains(
                re.escape(department), na=False
            )
        )
        result.loc[department_match, "match_score"] += 5

    if location:
        location_match = result["location"].str.lower().str.contains(
            re.escape(location), na=False
        )
        result.loc[location_match, "match_score"] += 8

    result["match_score"] = result["match_score"].clip(0, 100)

    result = result.sort_values(
        ["match_score"],
        ascending=False
    )

    return result.head(top_n).reset_index(drop=True)



# ============================================================
# COMPANY / TECHNICAL JOB FILTER
# ============================================================

EXCLUDED_TITLE_KEYWORDS = [
    "professor",
    "assistant professor",
    "associate professor",
    "lecturer",
    "teacher",
    "faculty",
    "teaching",
    "tutor",
    "trainer",
    "academic",
    "academics",
    "education",
    "school",
    "college",
    "university",
    "institute",
    "principal",
    "dean",
]

EXCLUDED_COMPANY_KEYWORDS = [
    "college",
    "university",
    "school",
    "educational society",
    "education",
    "academy",
    "polytechnic",
    "institute",
]


def filter_company_jobs(df):

    df = df.copy()

    # Make searchable text
    df["_title_text"] = (
        df["title"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    df["_company_text"] = (
        df["companyName"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    # --------------------------------------------------------
    # Remove teaching / academic jobs
    # --------------------------------------------------------

    title_pattern = "|".join(
        map(
            lambda x: x.replace(" ", r"\s+"),
            EXCLUDED_TITLE_KEYWORDS
        )
    )

    company_pattern = "|".join(
        map(
            lambda x: x.replace(" ", r"\s+"),
            EXCLUDED_COMPANY_KEYWORDS
        )
    )

    title_excluded = df["_title_text"].str.contains(
        title_pattern,
        regex=True,
        na=False
    )

    company_excluded = df["_company_text"].str.contains(
        company_pattern,
        regex=True,
        na=False
    )

    # Keep only company jobs
    df = df[
        ~title_excluded &
        ~company_excluded
    ].copy()

    # Remove helper columns
    df = df.drop(
        columns=[
            "_title_text",
            "_company_text"
        ],
        errors="ignore"
    )

    return df


# ============================================================
# BRANCH-WISE JOB FILTER
# ============================================================

BRANCH_KEYWORDS = {
    "cse": [
        "software", "developer", "development",
        "data analyst", "data engineer", "data scientist",
        "python", "java", "full stack", "frontend",
        "backend", "web developer", "cloud", "devops",
        "cyber security", "machine learning", "ai engineer",
        "qa", "testing", "database", "sql", "network",
        "technical support", "application"
    ],

    "ece": [
        "electronics", "embedded", "vlsi",
        "firmware", "hardware", "iot",
        "telecom", "electronics engineer",
        "embedded engineer", "pcb",
        "semiconductor", "electrical"
    ],

    "civil": [
        "civil engineer", "structural",
        "construction", "site engineer",
        "planning engineer", "quantity surveyor",
        "bim", "autocad", "civil",
        "project engineer", "design engineer"
    ],

    "mechanical": [
        "mechanical engineer", "mechanical",
        "manufacturing", "production engineer",
        "automotive", "cad", "design engineer",
        "maintenance engineer", "quality engineer",
        "hvac", "process engineer",
        "industrial engineer"
    ]
}


# ============================================================
# EXCLUDE ACADEMIC / TEACHING JOBS
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
    "academics",
    "education",
    "school",
    "college",
    "university",
    "institute",
    "principal",
    "dean"
]

ACADEMIC_COMPANY_KEYWORDS = [
    "college",
    "university",
    "school",
    "educational society",
    "education",
    "academy",
    "polytechnic",
    "institute"
]


def filter_branch_jobs(df, branch):

    df = df.copy()

    branch = str(branch).strip().lower()

    if branch not in BRANCH_KEYWORDS:
        return pd.DataFrame(columns=df.columns)

    # --------------------------------------------------------
    # Build searchable job text
    # --------------------------------------------------------

    for column in [
        "title",
        "tagsAndSkills",
        "jobDescription",
        "companyName"
    ]:

        if column not in df.columns:
            df[column] = ""

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.lower()
        )

    df["_job_text"] = (
        df["title"] + " " +
        df["tagsAndSkills"] + " " +
        df["jobDescription"]
    )

    # --------------------------------------------------------
    # Remove academic jobs
    # --------------------------------------------------------

    academic_pattern = "|".join(
        [
            keyword.replace(" ", r"\s+")
            for keyword in ACADEMIC_KEYWORDS
        ]
    )

    academic_company_pattern = "|".join(
        [
            keyword.replace(" ", r"\s+")
            for keyword in ACADEMIC_COMPANY_KEYWORDS
        ]
    )

    academic_title = df["title"].str.contains(
        academic_pattern,
        regex=True,
        na=False
    )

    academic_company = df["companyName"].str.contains(
        academic_company_pattern,
        regex=True,
        na=False
    )

    df = df[
        ~academic_title &
        ~academic_company
    ].copy()

    # --------------------------------------------------------
    # Keep branch-relevant jobs
    # --------------------------------------------------------

    branch_pattern = "|".join(
        [
            keyword.replace(" ", r"\s+")
            for keyword in BRANCH_KEYWORDS[branch]
        ]
    )

    branch_match = df["_job_text"].str.contains(
        branch_pattern,
        regex=True,
        na=False
    )

    df = df[branch_match].copy()

    # --------------------------------------------------------
    # Remove helper column
    # --------------------------------------------------------

    df = df.drop(
        columns=["_job_text"],
        errors="ignore"
    )

    return df