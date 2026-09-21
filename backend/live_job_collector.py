import re
from datetime import datetime, timezone

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models.live_job import LiveJob


# ============================================================
# CONFIG
# ============================================================

GREENHOUSE_COMPANIES = {
    # Add verified Greenhouse board tokens here.
}

LEVER_COMPANIES = {
    "Dun & Bradstreet": "dnb",
    "Drivetrain": "drivetrain",
    "JumpCloud": "jumpcloud",
    "Everbridge": "everbridge",
    "100ms": "100ms",
    "RapidAI": "rapidai",
    "Acceldata": "acceldata",
    "HighLevel": "gohighlevel",
    "Veeva Systems": "veeva",
    "Jobgether": "jobgether",
}


# ============================================================
# INDIA LOCATION FILTER
# ============================================================

INDIA_KEYWORDS = [
    "india",
    "bengaluru",
    "bangalore",
    "hyderabad",
    "chennai",
    "pune",
    "mumbai",
    "delhi",
    "gurugram",
    "gurgaon",
    "noida",
    "kolkata",
    "ahmedabad",
    "coimbatore",
    "kochi",
    "thiruvananthapuram",
    "jaipur",
    "indore",
]


# ============================================================
# ROLE FILTERS
# ============================================================

TECH_ROLE_KEYWORDS = [

    # CSE / IT / DATA
    "software engineer",
    "software developer",
    "data analyst",
    "data engineer",
    "data scientist",
    "machine learning engineer",
    "ml engineer",
    "ai engineer",
    "ai developer",
    "python developer",
    "java developer",
    "full stack developer",
    "full stack engineer",
    "backend developer",
    "backend engineer",
    "frontend developer",
    "frontend engineer",
    "cloud engineer",
    "devops engineer",
    "devops",
    "cyber security",
    "cybersecurity",
    "database engineer",
    "qa engineer",
    "automation engineer",
    "network engineer",

    # ECE
    "embedded engineer",
    "embedded software",
    "electronics engineer",
    "vlsi engineer",
    "firmware engineer",
    "iot engineer",
    "hardware engineer",
    "pcb engineer",
    "telecom engineer",
    "semiconductor engineer",

    # CIVIL
    "civil engineer",
    "structural engineer",
    "site engineer",
    "construction engineer",
    "planning engineer",
    "quantity surveyor",
    "bim engineer",
    "autocad",
    "project engineer",
    "civil design engineer",

    # MECHANICAL
    "mechanical engineer",
    "mechanical design engineer",
    "design engineer",
    "cad engineer",
    "manufacturing engineer",
    "production engineer",
    "automotive engineer",
    "maintenance engineer",
    "quality engineer",
    "hvac engineer",
    "process engineer",
    "industrial engineer",
]


# ============================================================
# ACADEMIC / NON-COMPANY ROLES
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
    "school",
    "college",
    "university",
    "principal",
    "dean",
]


# ============================================================
# DATE HELPERS
# ============================================================

def parse_lever_date(value):
    """
    Convert Lever Unix milliseconds
    into naive UTC datetime.
    """

    if value is None:
        return None

    try:
        return datetime.fromtimestamp(
            int(value) / 1000,
            tz=timezone.utc
        ).replace(tzinfo=None)

    except (
        ValueError,
        TypeError,
        OverflowError
    ):
        return None


def now_utc():
    """
    Current UTC time as naive datetime
    for PostgreSQL.
    """

    return datetime.now(
        timezone.utc
    ).replace(
        tzinfo=None
    )


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_text(value):
    """
    Remove HTML and normalize whitespace.
    """

    if value is None:
        return ""

    value = re.sub(
        r"<[^>]+>",
        " ",
        str(value)
    )

    return re.sub(
        r"\s+",
        " ",
        value
    ).strip()


def extract_lever_lists(job):
    """
    Flatten Lever structured list sections.
    """

    parts = []

    for item in job.get("lists", []) or []:

        if not isinstance(item, dict):
            continue

        heading = clean_text(
            item.get("text")
        )

        content = item.get("content")

        if isinstance(content, list):

            content_text = " ".join(
                clean_text(x)
                for x in content
            )

        else:

            content_text = clean_text(
                content
            )

        if heading:
            parts.append(heading)

        if content_text:
            parts.append(content_text)

    return " ".join(parts)


def extract_lever_additional(job):
    """
    Flatten Lever additional information.
    """

    additional = job.get(
        "additional"
    )

    if isinstance(additional, list):

        return " ".join(
            clean_text(x)
            for x in additional
        )

    return clean_text(
        additional
    )


# ============================================================
# SKILL EXTRACTION
# ============================================================

def extract_skills_from_text(text):

    text_lower = text.lower()

    skills = [
        "python",
        "sql",
        "java",
        "javascript",
        "typescript",
        "c++",
        "c#",
        "react",
        "node.js",
        "nodejs",
        "angular",
        "html",
        "css",
        "pandas",
        "numpy",
        "scikit-learn",
        "tensorflow",
        "pytorch",
        "machine learning",
        "deep learning",
        "generative ai",
        "llm",
        "artificial intelligence",
        "data science",
        "data analytics",
        "spark",
        "pyspark",
        "hadoop",
        "kafka",
        "airflow",
        "aws",
        "azure",
        "gcp",
        "s3",
        "redshift",
        "lambda",
        "glue",
        "docker",
        "kubernetes",
        "terraform",
        "devops",
        "postgresql",
        "mysql",
        "mongodb",
        "snowflake",
        "databricks",
        "etl",
        "elt",
        "api",
        "rest api",
        "cyber security",
        "cybersecurity",
        "network security",
        "embedded",
        "firmware",
        "iot",
        "vlsi",
        "electronics",
        "autocad",
        "bim",
        "structural engineering",
        "civil engineering",
        "mechanical engineering",
        "cad",
        "manufacturing",
        "automotive",
    ]

    found = []

    for skill in skills:

        pattern = (
            r"(?<!\w)"
            + re.escape(skill)
            + r"(?!\w)"
        )

        if re.search(
            pattern,
            text_lower
        ):
            found.append(skill)

    if not found:
        return None

    return ", ".join(found)


# ============================================================
# EXPERIENCE EXTRACTION
# ============================================================

def extract_experience_from_text(text):

    text = clean_text(text)

    patterns = [

        r"\b(\d+)\s*(?:-|to)\s*(\d+)\s*(?:years?|yrs?)\b",

        r"\b(\d+)\s*\+\s*(?:years?|yrs?)\b",

        r"\bminimum\s+(\d+)\s*(?:years?|yrs?)\b",

        r"\b(\d+)\s*(?:years?|yrs?)\s+(?:of\s+)?experience\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if not match:
            continue

        groups = match.groups()

        if (
            len(groups) >= 2
            and groups[1]
        ):
            return (
                f"{groups[0]}-{groups[1]} years"
            )

        return f"{groups[0]}+ years"

    return None


# ============================================================
# WORK MODE EXTRACTION
# ============================================================

def extract_work_mode_from_text(text):

    text_lower = clean_text(
        text
    ).lower()

    if re.search(
        r"\bhybrid\b",
        text_lower
    ):
        return "Hybrid"

    if re.search(
        r"\b(?:fully\s+)?remote\b",
        text_lower
    ):
        return "Remote"

    if re.search(
        r"\b(?:on[- ]?site|onsite|office[- ]?based)\b",
        text_lower
    ):
        return "On-site"

    return None


# ============================================================
# SALARY EXTRACTION
# ============================================================

def extract_salary_from_lever(
    job,
    text
):

    salary_range = job.get(
        "salaryRange"
    )

    if isinstance(
        salary_range,
        dict
    ):

        minimum = salary_range.get(
            "min"
        )

        maximum = salary_range.get(
            "max"
        )

        currency = salary_range.get(
            "currency"
        )

        interval = salary_range.get(
            "interval"
        )

        if (
            minimum is not None
            and maximum is not None
        ):

            result = (
                f"{minimum}-{maximum}"
            )

            if currency:
                result += (
                    f" {currency}"
                )

            if interval:
                result += (
                    f" per {interval}"
                )

            return result

    match = re.search(
        r"(?i)\b(?:salary|compensation|pay)\b.{0,80}"
        r"(?:₹|rs\.?|inr|\$|usd|eur|gbp)\s*[\d,]+"
        r"(?:\s*[-–]\s*[\d,]+)?",
        text
    )

    if match:
        return clean_text(
            match.group(0)
        )

    return None


# ============================================================
# JOB FILTER
# ============================================================

def is_relevant_job(
    title,
    description=""
):

    title = str(
        title or ""
    )

    description = str(
        description or ""
    )

    text = (
        f"{title} {description}"
        .lower()
    )

    # Remove academic / education jobs
    for keyword in ACADEMIC_KEYWORDS:

        if keyword in text:
            return False

    # Keep only target technical roles
    for keyword in TECH_ROLE_KEYWORDS:

        if keyword in text:
            return True

    return False


# ============================================================
# LOCATION HELPERS
# ============================================================

def extract_location(location):

    if isinstance(
        location,
        dict
    ):
        return location.get(
            "name",
            ""
        )

    return str(
        location or ""
    )


def is_india_location(location):

    location_lower = str(
        location or ""
    ).lower()

    return any(
        keyword in location_lower
        for keyword in INDIA_KEYWORDS
    )


# ============================================================
# GREENHOUSE JOBS
# ============================================================

def fetch_greenhouse_jobs(
    company_name,
    board_token
):

    url = (
        "https://boards-api.greenhouse.io/"
        f"v1/boards/{board_token}/jobs"
    )

    params = {
        "content": "true"
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    jobs = []

    for job in data.get(
        "jobs",
        []
    ):

        title = job.get(
            "title",
            ""
        )

        description = clean_text(
            job.get(
                "content",
                ""
            )
        )

        if not is_relevant_job(
            title,
            description
        ):
            continue

        departments = job.get(
            "departments",
            []
        )

        department = ", ".join(
            d.get(
                "name",
                ""
            )
            for d in departments
            if d.get("name")
        )

        location = extract_location(
            job.get(
                "location",
                {}
            )
        )

        if not is_india_location(
            location
        ):
            continue

        full_text = (
            f"{title} {description}"
        )

        jobs.append({

            "source": "Greenhouse",

            "source_job_id": str(
                job.get("id")
            ),

            "company_name":
                company_name,

            "job_title":
                title,

            "department":
                department,

            "skills":
                extract_skills_from_text(
                    full_text
                ),

            "experience":
                extract_experience_from_text(
                    full_text
                ),

            "salary":
                None,

            "location":
                location,

            "work_mode":
                extract_work_mode_from_text(
                    full_text
                ),

            "job_description":
                description,

            "posted_date":
                None,

            "updated_date":
                None,

            "application_url":
                job.get(
                    "absolute_url"
                ),

            "status":
                "open",

            "last_checked":
                now_utc(),
        })

    return jobs


# ============================================================
# LEVER JOBS
# ============================================================

def fetch_lever_jobs(
    company_name,
    site_name
):

    url = (
        "https://api.lever.co/v0/postings/"
        f"{site_name}"
    )

    params = {
        "mode": "json"
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    jobs = []

    for job in data:

        title = job.get(
            "text",
            ""
        )

        description = clean_text(
            job.get(
                "descriptionPlain",
                ""
            )
        )

        lever_lists = (
            extract_lever_lists(job)
        )

        lever_additional = (
            extract_lever_additional(job)
        )

        full_detail_text = " ".join(
            part
            for part in [
                title,
                description,
                lever_lists,
                lever_additional
            ]
            if part
        )

        if not is_relevant_job(
            title,
            full_detail_text
        ):
            continue

        categories = job.get(
            "categories",
            {}
        )

        location = categories.get(
            "location",
            ""
        )

        if not is_india_location(
            location
        ):
            continue

        department = categories.get(
            "department",
            ""
        )

        posted_date = (
            parse_lever_date(
                job.get("createdAt")
            )
        )

        updated_date = (
            parse_lever_date(
                job.get("updatedAt")
            )
        )

        skills = (
            extract_skills_from_text(
                full_detail_text
            )
        )

        experience = (
            extract_experience_from_text(
                full_detail_text
            )
        )

        salary = (
            extract_salary_from_lever(
                job,
                full_detail_text
            )
        )

        work_mode = (
            extract_work_mode_from_text(
                full_detail_text
            )
        )

        jobs.append({

            "source":
                "Lever",

            "source_job_id":
                str(
                    job.get("id")
                ),

            "company_name":
                company_name,

            "job_title":
                title,

            "department":
                department,

            "skills":
                skills,

            "experience":
                experience,

            "salary":
                salary,

            "location":
                location,

            "work_mode":
                work_mode,

            "job_description":
                full_detail_text,

            "posted_date":
                posted_date,

            "updated_date":
                updated_date,

            "application_url":
                job.get(
                    "hostedUrl"
                ),

            "status":
                "open",

            "last_checked":
                now_utc(),
        })

    return jobs


# ============================================================
# COLLECT ALL LIVE JOBS
# ============================================================

def collect_live_jobs():

    all_jobs = []

    # Tracks which ATS/company was successfully checked.
    # This is important because we should NOT close jobs
    # when an API request itself failed.
    successful_companies = set()

    # ----------------------------
    # GREENHOUSE
    # ----------------------------

    for company, token in (
        GREENHOUSE_COMPANIES.items()
    ):

        try:

            jobs = fetch_greenhouse_jobs(
                company,
                token
            )

            all_jobs.extend(
                jobs
            )

            successful_companies.add(
                ("Greenhouse", company)
            )

            print(
                f"[Greenhouse] "
                f"{company}: "
                f"{len(jobs)} relevant jobs"
            )

        except Exception as e:

            print(
                f"[ERROR] Greenhouse "
                f"{company}: {e}"
            )

    # ----------------------------
    # LEVER
    # ----------------------------

    for company, site in (
        LEVER_COMPANIES.items()
    ):

        try:

            jobs = fetch_lever_jobs(
                company,
                site
            )

            all_jobs.extend(
                jobs
            )

            successful_companies.add(
                ("Lever", company)
            )

            print(
                f"[Lever] "
                f"{company}: "
                f"{len(jobs)} relevant jobs"
            )

        except Exception as e:

            print(
                f"[ERROR] Lever "
                f"{company}: {e}"
            )

    return all_jobs, successful_companies


# ============================================================
# JOB HISTORY HELPERS
# ============================================================

def insert_job_history(
    db,
    job,
    status,
    first_seen_at=None,
    last_seen_at=None,
    closed_at=None,
    collection_run_id=None
):
    """
    Insert one ATS observation into job_history.

    Every successful collector run creates a historical
    observation. This allows us to reconstruct recruitment
    activity over time.
    """

    observed_at = now_utc()

    if first_seen_at is None:
        first_seen_at = observed_at

    if last_seen_at is None:
        last_seen_at = observed_at

    db.execute(
        text(
            """
            INSERT INTO job_history (
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
            )
            VALUES (
                :job_id,
                :company_name,
                :job_title,
                :department,
                :skills,
                :experience,
                :salary,
                :location,
                :work_mode,
                :job_description,
                :application_url,
                :source,
                :source_job_id,
                :status,
                :observed_at,
                :first_seen_at,
                :last_seen_at,
                :closed_at,
                :collection_run_id
            )
            """
        ),
        {
            "job_id": job.get(
                "source_job_id"
            ),

            "company_name": job.get(
                "company_name"
            ),

            "job_title": job.get(
                "job_title"
            ),

            "department": job.get(
                "department"
            ),

            "skills": job.get(
                "skills"
            ),

            "experience": job.get(
                "experience"
            ),

            "salary": job.get(
                "salary"
            ),

            "location": job.get(
                "location"
            ),

            "work_mode": job.get(
                "work_mode"
            ),

            "job_description": job.get(
                "job_description"
            ),

            "application_url": job.get(
                "application_url"
            ),

            "source": job.get(
                "source"
            ),

            "source_job_id": job.get(
                "source_job_id"
            ),

            "status": status,

            "observed_at": observed_at,

            "first_seen_at":
                first_seen_at,

            "last_seen_at":
                last_seen_at,

            "closed_at":
                closed_at,
                
            "collection_run_id":
                collection_run_id,
        }
    )


def get_job_history_dates(
    db,
    source,
    source_job_id,
    observed_at
):
    """
    Get first/last observation dates for a job.
    """

    result = db.execute(
        text(
            """
            SELECT
                MIN(observed_at) AS first_seen,
                MAX(observed_at) AS last_seen
            FROM job_history
            WHERE source = :source
              AND source_job_id = :source_job_id
            """
        ),
        {
            "source": source,
            "source_job_id": source_job_id,
        }
    ).fetchone()

    first_seen = (
        result.first_seen
        if result and result.first_seen
        else observed_at
    )

    last_seen = (
        result.last_seen
        if result and result.last_seen
        else observed_at
    )

    return first_seen, last_seen


# ============================================================
# SAVE LIVE JOBS + ATS HISTORY
# ============================================================

def save_live_jobs_to_database(
    jobs,
    successful_companies
):
    collection_run_id = now_utc().strftime("%Y%m%d%H%M%S")
    db: Session = SessionLocal()

    try:

        inserted = 0
        updated = 0
        history_inserted = 0
        closed = 0

        current_job_keys = set()

        # ====================================================
        # SAVE CURRENT OPEN JOBS
        # ====================================================

        for job in jobs:

            source = job.get(
                "source"
            )

            source_job_id = job.get(
                "source_job_id"
            )

            company_name = job.get(
                "company_name"
            )

            if not source_job_id:
                continue

            job_key = (
                source,
                source_job_id
            )

            current_job_keys.add(
                job_key
            )

            existing_job = (
                db.query(LiveJob)
                .filter(
                    LiveJob.source == source,
                    LiveJob.source_job_id
                    == source_job_id
                )
                .first()
            )

            if existing_job:

                existing_job.job_id = (
                    source_job_id
                )

                existing_job.company_name = (
                    company_name
                )

                existing_job.job_title = (
                    job.get(
                        "job_title"
                    )
                )

                existing_job.department = (
                    job.get(
                        "department"
                    )
                )

                existing_job.skills = (
                    job.get(
                        "skills"
                    )
                )

                existing_job.experience = (
                    job.get(
                        "experience"
                    )
                )

                existing_job.salary = (
                    job.get(
                        "salary"
                    )
                )

                existing_job.location = (
                    job.get(
                        "location"
                    )
                )

                existing_job.work_mode = (
                    job.get(
                        "work_mode"
                    )
                )

                existing_job.job_description = (
                    job.get(
                        "job_description"
                    )
                )

                existing_job.posted_date = (
                    job.get(
                        "posted_date"
                    )
                )

                existing_job.updated_date = (
                    job.get(
                        "updated_date"
                    )
                )

                existing_job.application_url = (
                    job.get(
                        "application_url"
                    )
                )

                existing_job.status = "open"

                existing_job.last_checked = (
                    job.get(
                        "last_checked"
                    )
                )

                updated += 1

            else:

                new_job = LiveJob(

                    job_id=
                        source_job_id,

                    company_name=
                        company_name,

                    job_title=
                        job.get(
                            "job_title"
                        ),

                    department=
                        job.get(
                            "department"
                        ),

                    skills=
                        job.get(
                            "skills"
                        ),

                    experience=
                        job.get(
                            "experience"
                        ),

                    salary=
                        job.get(
                            "salary"
                        ),

                    location=
                        job.get(
                            "location"
                        ),

                    work_mode=
                        job.get(
                            "work_mode"
                        ),

                    job_description=
                        job.get(
                            "job_description"
                        ),

                    posted_date=
                        job.get(
                            "posted_date"
                        ),

                    updated_date=
                        job.get(
                            "updated_date"
                        ),

                    application_url=
                        job.get(
                            "application_url"
                        ),

                    source=
                        source,

                    source_job_id=
                        source_job_id,

                    status=
                        "open",

                    last_checked=
                        job.get(
                            "last_checked"
                        )
                )

                db.add(
                    new_job
                )

                inserted += 1

            # -----------------------------------------------
            # HISTORY
            # -----------------------------------------------

            observed_at = now_utc()

            first_seen, last_seen = (
                get_job_history_dates(
                    db,
                    source,
                    source_job_id,
                    observed_at
                )
            )

            insert_job_history(
                db=db,
                job=job,
                status="open",
                first_seen_at=first_seen,
                last_seen_at=observed_at,
                closed_at=None,
                collection_run_id=collection_run_id
)

            history_inserted += 1

        db.flush()

        # ====================================================
        # DETECT CLOSED JOBS
        # ====================================================
        #
        # Only check companies whose ATS endpoint was
        # successfully fetched.
        #
        # If an API failed, we do NOT mark that company's
        # existing jobs as closed.
        # ====================================================

        open_jobs = (
            db.query(LiveJob)
            .filter(
                LiveJob.status == "open"
            )
            .all()
        )

        for existing_job in open_jobs:

            company_key = (
                existing_job.source,
                existing_job.company_name
            )

            if company_key not in successful_companies:
                continue

            job_key = (
                existing_job.source,
                existing_job.source_job_id
            )

            if job_key in current_job_keys:
                continue

            # -----------------------------------------------
            # Job disappeared from ATS
            # -----------------------------------------------

            closed_at = now_utc()

            existing_job.status = (
                "closed"
            )

            existing_job.last_checked = (
                closed_at
            )

            closed += 1

            # Create closure history snapshot
            history_job = {

                "source":
                    existing_job.source,

                "source_job_id":
                    existing_job.source_job_id,

                "company_name":
                    existing_job.company_name,

                "job_title":
                    existing_job.job_title,

                "department":
                    existing_job.department,

                "skills":
                    existing_job.skills,

                "experience":
                    existing_job.experience,

                "salary":
                    existing_job.salary,

                "location":
                    existing_job.location,

                "work_mode":
                    existing_job.work_mode,

                "job_description":
                    existing_job.job_description,

                "application_url":
                    existing_job.application_url,
            }

            first_seen, last_seen = (
                get_job_history_dates(
                    db,
                    existing_job.source,
                    existing_job.source_job_id,
                    closed_at
                )
            )

            insert_job_history(
                db=db,
                job=history_job,
                status="closed",
                first_seen_at=first_seen,
                last_seen_at=last_seen,
                closed_at=closed_at,
                collection_run_id=collection_run_id
)

            history_inserted += 1

        # ====================================================
        # COMMIT
        # ====================================================

        db.commit()

        total_current_open = (
            db.query(LiveJob)
            .filter(
                LiveJob.status == "open"
            )
            .count()
        )

        total_history = db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM job_history
                """
            )
        ).scalar()

        print(
            "\n======================================"
        )

        print(
            "ATS JOB DATABASE UPDATE"
        )

        print(
            "======================================"
        )

        print(
            f"Inserted current jobs : {inserted}"
        )

        print(
            f"Updated current jobs  : {updated}"
        )

        print(
            f"Closed jobs           : {closed}"
        )

        print(
            f"History records added : {history_inserted}"
        )

        print(
            f"Current open jobs     : "
            f"{total_current_open}"
        )

        print(
            f"Total history records : "
            f"{total_history}"
        )

        print(
            "======================================"
        )

    except Exception as e:

        db.rollback()

        print(
            "\n[DATABASE ERROR]"
        )

        print(e)

        raise

    finally:

        db.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    jobs, successful_companies = (
        collect_live_jobs()
    )

    print(
        f"\nTotal live relevant jobs: "
        f"{len(jobs)}"
    )

    print(
        f"Successfully checked ATS companies: "
        f"{len(successful_companies)}"
    )

    # ========================================================
    # DETAIL CHECK
    # ========================================================

    if jobs:

        print(
            "\nLIVE JOB DETAIL EXTRACTION CHECK"
        )

        print(
            "--------------------------------"
        )

        for job in jobs[:5]:

            print(
                f"Title      : "
                f"{job.get('job_title')}"
            )

            print(
                f"Company    : "
                f"{job.get('company_name')}"
            )

            print(
                f"Skills     : "
                f"{job.get('skills')}"
            )

            print(
                f"Experience : "
                f"{job.get('experience')}"
            )

            print(
                f"Salary     : "
                f"{job.get('salary')}"
            )

            print(
                f"Work mode  : "
                f"{job.get('work_mode')}"
            )

            print(
                f"Location   : "
                f"{job.get('location')}"
            )

            print(
                f"Apply URL  : "
                f"{job.get('application_url')}"
            )

            print(
                "--------------------------------"
            )

        # ====================================================
        # DATABASE SAVE
        # ====================================================

        save_live_jobs_to_database(
            jobs,
            successful_companies
        )

    else:

        print(
            "\nNo live relevant jobs found."
        )

        # Even if zero jobs are returned, we should NOT
        # automatically close jobs because this could be
        # caused by filtering/API problems.
        print(
            "No database status changes were made."
        )