import re

import pandas as pd
import streamlit as st
import plotly.express as px

from sqlalchemy import text
from backend.database import engine


# ============================================================
# CONFIG
# ============================================================

REFERENCE_FILE = "data/indian-job-market-dataset-2025.xlsx"


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):
    if pd.isna(value):
        return ""

    value = str(value).lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize_role(title):
    """
    Convert detailed job titles into broader role groups.
    """

    title = clean_text(title)

    role_keywords = {
        "Data Scientist": [
            "data scientist",
            "data science"
        ],
        "Data Analyst": [
            "data analyst",
            "business analyst",
            "analytics analyst"
        ],
        "Machine Learning Engineer": [
            "machine learning engineer",
            "ml engineer",
            "machine learning"
        ],
        "AI Engineer": [
            "ai engineer",
            "artificial intelligence engineer",
            "ai developer"
        ],
        "Software Engineer": [
            "software engineer",
            "software developer",
            "application developer"
        ],
        "Python Developer": [
            "python developer",
            "python engineer"
        ],
        "Backend Developer": [
            "backend developer",
            "backend engineer"
        ],
        "Frontend Developer": [
            "frontend developer",
            "front end developer"
        ],
        "Full Stack Developer": [
            "full stack developer",
            "fullstack developer"
        ],
        "DevOps Engineer": [
            "devops engineer",
            "devops"
        ],
        "Cloud Engineer": [
            "cloud engineer",
            "cloud developer"
        ],
        "Data Engineer": [
            "data engineer"
        ],
        "Database Engineer": [
            "database engineer",
            "database developer"
        ],
        "Cybersecurity Engineer": [
            "cyber security",
            "cybersecurity",
            "security engineer"
        ],
        "Network Engineer": [
            "network engineer"
        ],
        "QA Engineer": [
            "qa engineer",
            "quality analyst",
            "quality assurance"
        ]
    }

    for role, keywords in role_keywords.items():
        for keyword in keywords:
            if keyword in title:
                return role

    return "Other"


# ============================================================
# LOAD REFERENCE DATA
# ============================================================

@st.cache_data(ttl=600)
def load_reference_jobs():

    try:

        df = pd.read_excel(
            REFERENCE_FILE
        )

        required_columns = [
            "title",
            "companyName",
            "jobUploaded",
            "location",
            "tagsAndSkills"
        ]

        missing = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing:

            st.error(
                f"Missing columns: {missing}"
            )

            return pd.DataFrame()

        df = df.copy()

        df["title"] = (
            df["title"]
            .fillna("")
            .astype(str)
        )

        df["companyName"] = (
            df["companyName"]
            .fillna("")
            .astype(str)
        )

        df["jobUploaded"] = (
            df["jobUploaded"]
            .fillna("")
            .astype(str)
        )

        df["role"] = (
            df["title"]
            .apply(normalize_role)
        )

        df["title_clean"] = (
            df["title"]
            .apply(clean_text)
        )

        df["company_clean"] = (
            df["companyName"]
            .apply(clean_text)
        )

        return df

    except Exception as e:

        st.error(
            f"Unable to load reference dataset: {e}"
        )

        return pd.DataFrame()


# ============================================================
# LOAD LIVE JOBS
# ============================================================

@st.cache_data(ttl=120)
def load_live_jobs():

    query = text("""
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
    """)

    try:

        with engine.connect() as connection:

            df = pd.read_sql(
                query,
                connection
            )

        if not df.empty:

            # Clean important text columns
            text_columns = [
                "company_name",
                "job_title",
                "department",
                "location",
                "work_mode",
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

            # Normalize role
            df["role"] = (
                df["job_title"]
                .apply(normalize_role)
            )

            # Date conversion
            df["posted_date"] = pd.to_datetime(
                df["posted_date"],
                errors="coerce"
            )

        return df

    except Exception as e:

        st.error(
            f"Unable to load live jobs: {e}"
        )

        return pd.DataFrame()


# ============================================================
# CURRENT JOB DEMAND
# ============================================================

def build_current_role_demand(live_df):

    if live_df.empty:
        return pd.DataFrame()

    current = (
        live_df[
            live_df["role"] != "Other"
        ]
        .groupby("role")
        .agg(
            current_openings=(
                "job_id",
                "count"
            ),
            companies_hiring=(
                "company_name",
                "nunique"
            )
        )
        .reset_index()
    )

    return (
        current
        .sort_values(
            "current_openings",
            ascending=False
        )
        .reset_index(drop=True)
    )


def build_company_demand(live_df):

    if live_df.empty:
        return pd.DataFrame()

    company_df = (
        live_df[
            live_df["company_name"].str.strip() != ""
        ]
        .groupby("company_name")
        .size()
        .reset_index(
            name="openings"
        )
        .sort_values(
            "openings",
            ascending=False
        )
        .reset_index(drop=True)
    )

    return company_df


def build_department_demand(live_df):

    if live_df.empty:
        return pd.DataFrame()

    department_df = (
        live_df[
            live_df["department"].str.strip() != ""
        ]
        .groupby("department")
        .size()
        .reset_index(
            name="openings"
        )
        .sort_values(
            "openings",
            ascending=False
        )
        .reset_index(drop=True)
    )

    return department_df


def build_location_demand(live_df):

    if live_df.empty:
        return pd.DataFrame()

    location_df = (
        live_df[
            live_df["location"].str.strip() != ""
        ]
        .groupby("location")
        .size()
        .reset_index(
            name="openings"
        )
        .sort_values(
            "openings",
            ascending=False
        )
        .reset_index(drop=True)
    )

    return location_df


# ============================================================
# HISTORICAL + CURRENT ROLE DEMAND
# ============================================================

def build_role_demand(
    reference_df,
    live_df
):

    if reference_df.empty:

        return pd.DataFrame()

    historical = (
        reference_df[
            reference_df["role"] != "Other"
        ]
        .groupby("role")
        .agg(
            historical_posts=(
                "title",
                "size"
            ),
            historical_companies=(
                "companyName",
                "nunique"
            )
        )
        .reset_index()
    )

    if live_df.empty:

        historical["current_openings"] = 0

    else:

        current = (
            live_df[
                live_df["role"] != "Other"
            ]
            .groupby("role")
            .size()
            .reset_index(
                name="current_openings"
            )
        )

        historical = historical.merge(
            current,
            on="role",
            how="left"
        )

        historical["current_openings"] = (
            historical["current_openings"]
            .fillna(0)
            .astype(int)
        )

    # --------------------------------------------------------
    # Demand score
    # --------------------------------------------------------

    max_posts = max(
        historical["historical_posts"].max(),
        1
    )

    max_companies = max(
        historical["historical_companies"].max(),
        1
    )

    max_openings = max(
        historical["current_openings"].max(),
        1
    )

    historical["posting_score"] = (
        historical["historical_posts"]
        / max_posts
        * 100
    )

    historical["company_score"] = (
        historical["historical_companies"]
        / max_companies
        * 100
    )

    historical["opening_score"] = (
        historical["current_openings"]
        / max_openings
        * 100
    )

    historical["demand_score"] = (
        historical["posting_score"] * 0.50
        +
        historical["company_score"] * 0.30
        +
        historical["opening_score"] * 0.20
    )

    historical["demand_score"] = (
        historical["demand_score"]
        .round(2)
    )

    return (
        historical
        .sort_values(
            "demand_score",
            ascending=False
        )
        .reset_index(drop=True)
    )


# ============================================================
# HIRING ACTIVITY PROBABILITY
# ============================================================

def calculate_hiring_probability(
    role_row
):

    historical_posts = float(
        role_row["historical_posts"]
    )

    historical_companies = float(
        role_row["historical_companies"]
    )

    current_openings = float(
        role_row["current_openings"]
    )

    # --------------------------------------------------------
    # Normalize signals
    # --------------------------------------------------------

    posting_signal = min(
        historical_posts / 5000,
        1
    ) * 100

    company_signal = min(
        historical_companies / 500,
        1
    ) * 100

    opening_signal = min(
        current_openings / 25,
        1
    ) * 100

    # --------------------------------------------------------
    # Estimated probability
    # --------------------------------------------------------

    probability = (
        posting_signal * 0.45
        +
        company_signal * 0.25
        +
        opening_signal * 0.30
    )

    probability = max(
        0,
        min(
            probability,
            100
        )
    )

    return round(
        probability,
        1
    )


# ============================================================
# MAIN PAGE
# ============================================================

def show_future_hiring():

    st.title(
        "🔮 Future Hiring Analytics"
    )

    st.caption(
        "Current job demand, in-demand roles and "
        "estimated future hiring activity."
    )

    # ========================================================
    # LOAD DATA
    # ========================================================

    reference_df = load_reference_jobs()

    live_df = load_live_jobs()

    if reference_df.empty:

        st.error(
            "Reference job-market dataset is unavailable."
        )

        return

    if live_df.empty:

        st.warning(
            "No open live jobs are currently available."
        )

    # ========================================================
    # CURRENT JOB DEMAND
    # ========================================================

    st.header(
        "📊 Current Job Demand"
    )

    total_open_jobs = (
        len(live_df)
        if not live_df.empty
        else 0
    )

    current_role_df = build_current_role_demand(
        live_df
    )

    current_companies = (
        live_df["company_name"]
        .replace("", pd.NA)
        .dropna()
        .nunique()
        if not live_df.empty
        else 0
    )

    current_roles = (
        current_role_df["role"].nunique()
        if not current_role_df.empty
        else 0
    )

    # --------------------------------------------------------
    # CURRENT DEMAND METRICS
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Open Jobs",
            f"{total_open_jobs:,}"
        )

    with c2:

        st.metric(
            "In-Demand Roles",
            f"{current_roles:,}"
        )

    with c3:

        st.metric(
            "Companies Hiring",
            f"{current_companies:,}"
        )

    with c4:

        departments = (
            live_df["department"]
            .replace("", pd.NA)
            .dropna()
            .nunique()
            if not live_df.empty
            else 0
        )

        st.metric(
            "Departments",
            f"{departments:,}"
        )

    # ========================================================
    # CURRENT JOB DEMAND BY ROLE
    # ========================================================

    st.subheader(
        "📈 Current Job Demand by Role"
    )

    if current_role_df.empty:

        st.info(
            "No normalized roles are available "
            "from the current live jobs."
        )

    else:

        role_chart = (
            current_role_df
            .head(10)
            .sort_values(
                "current_openings",
                ascending=True
            )
        )

        fig_current_roles = px.bar(
            role_chart,
            x="current_openings",
            y="role",
            orientation="h",
            text="current_openings",
            labels={
                "current_openings": "Current Openings",
                "role": "Role"
            },
            title="Top Current Job Demand by Role"
        )

        fig_current_roles.update_traces(
            textposition="outside"
        )

        fig_current_roles.update_layout(
            height=500,
            margin=dict(
                l=20,
                r=40,
                t=70,
                b=20
            )
        )

        st.plotly_chart(
            fig_current_roles,
            use_container_width=True
        )

    # ========================================================
    # CURRENT IN-DEMAND ROLES TABLE
    # ========================================================

    st.subheader(
        "💼 Current In-Demand Roles"
    )

    if current_role_df.empty:

        st.info(
            "No current role-demand data available."
        )

    else:

        role_table = (
            current_role_df
            .copy()
        )

        role_table["Demand Share"] = (
            role_table["current_openings"]
            / max(
                role_table["current_openings"].sum(),
                1
            )
            * 100
        ).round(1)

        role_table = role_table[
            [
                "role",
                "current_openings",
                "companies_hiring",
                "Demand Share"
            ]
        ]

        role_table.columns = [
            "Role",
            "Current Openings",
            "Companies Hiring",
            "Demand Share (%)"
        ]

        st.dataframe(
            role_table,
            use_container_width=True,
            hide_index=True
        )

    # ========================================================
    # COMPANY DEMAND
    # ========================================================

    st.subheader(
        "🏢 Current Hiring Demand by Company"
    )

    company_df = build_company_demand(
        live_df
    )

    if company_df.empty:

        st.info(
            "No company-level demand data available."
        )

    else:

        company_chart = (
            company_df
            .head(10)
            .sort_values(
                "openings",
                ascending=True
            )
        )

        fig_company = px.bar(
            company_chart,
            x="openings",
            y="company_name",
            orientation="h",
            text="openings",
            labels={
                "openings": "Current Openings",
                "company_name": "Company"
            },
            title="Companies with Current Job Openings"
        )

        fig_company.update_traces(
            textposition="outside"
        )

        fig_company.update_layout(
            height=500
        )

        st.plotly_chart(
            fig_company,
            use_container_width=True
        )

    # ========================================================
    # DEPARTMENT DEMAND
    # ========================================================

    st.subheader(
        "🏫 Current Job Demand by Department"
    )

    department_df = build_department_demand(
        live_df
    )

    if department_df.empty:

        st.info(
            "No department-level demand data available."
        )

    else:

        department_chart = (
            department_df
            .head(10)
            .sort_values(
                "openings",
                ascending=True
            )
        )

        fig_department = px.bar(
            department_chart,
            x="openings",
            y="department",
            orientation="h",
            text="openings",
            labels={
                "openings": "Current Openings",
                "department": "Department"
            },
            title="Current Job Demand by Department"
        )

        fig_department.update_traces(
            textposition="outside"
        )

        fig_department.update_layout(
            height=450
        )

        st.plotly_chart(
            fig_department,
            use_container_width=True
        )

    # ========================================================
    # LOCATION DEMAND
    # ========================================================

    st.subheader(
        "📍 Current Job Demand by Location"
    )

    location_df = build_location_demand(
        live_df
    )

    if location_df.empty:

        st.info(
            "No location-level demand data available."
        )

    else:

        location_chart = (
            location_df
            .head(10)
            .sort_values(
                "openings",
                ascending=True
            )
        )

        fig_location = px.bar(
            location_chart,
            x="openings",
            y="location",
            orientation="h",
            text="openings",
            labels={
                "openings": "Current Openings",
                "location": "Location"
            },
            title="Current Job Demand by Location"
        )

        fig_location.update_traces(
            textposition="outside"
        )

        fig_location.update_layout(
            height=500
        )

        st.plotly_chart(
            fig_location,
            use_container_width=True
        )

    # ========================================================
    # SEPARATOR
    # ========================================================

    st.divider()

    # ========================================================
    # HISTORICAL + FUTURE HIRING ANALYSIS
    # ========================================================

    st.header(
        "🔮 Future Hiring Analysis"
    )

    st.caption(
        "Historical job-posting activity combined with "
        "current live openings."
    )

    st.info(
        "The probability shown below is an estimated "
        "hiring-activity probability based on job-posting "
        "demand, company participation and current live "
        "openings. It is not a guaranteed individual "
        "hiring probability."
    )

    demand_df = build_role_demand(
        reference_df,
        live_df
    )

    if demand_df.empty:

        st.warning(
            "No role-demand information available."
        )

        return

    # ========================================================
    # HISTORICAL DEMANDED ROLES
    # ========================================================

    st.subheader(
        "📈 Historical Most Demanded Roles"
    )

    historical_chart = (
        demand_df
        .head(10)
        .sort_values(
            "historical_posts",
            ascending=True
        )
    )

    fig = px.bar(
        historical_chart,
        x="historical_posts",
        y="role",
        orientation="h",
        labels={
            "historical_posts":
                "Historical Job Postings",
            "role":
                "Role"
        },
        title="Historical Job Posting Demand"
    )

    fig.update_layout(
        height=500
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ========================================================
    # CURRENT OPENINGS FOR HISTORICAL DEMANDED ROLES
    # ========================================================

    st.subheader(
        "💼 Current Openings for Demanded Roles"
    )

    current_chart = (
        demand_df[
            demand_df["current_openings"] > 0
        ]
        .head(10)
        .sort_values(
            "current_openings",
            ascending=True
        )
    )

    if current_chart.empty:

        st.info(
            "No current live openings found "
            "for the analyzed roles."
        )

    else:

        fig2 = px.bar(
            current_chart,
            x="current_openings",
            y="role",
            orientation="h",
            labels={
                "current_openings":
                    "Current Live Openings",
                "role":
                    "Role"
            },
            title="Current Openings for Historically Demanded Roles"
        )

        fig2.update_layout(
            height=500
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    # ========================================================
    # DEMAND SCORE
    # ========================================================

    st.subheader(
        "📊 Role Demand Score"
    )

    score_chart = (
        demand_df
        .head(10)
        .sort_values(
            "demand_score",
            ascending=True
        )
    )

    fig3 = px.bar(
        score_chart,
        x="demand_score",
        y="role",
        orientation="h",
        labels={
            "demand_score":
                "Demand Score",
            "role":
                "Role"
        },
        title="Combined Historical + Current Demand Score"
    )

    fig3.update_layout(
        height=500
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

    # ========================================================
    # ROLE SELECTION
    # ========================================================

    st.divider()

    st.subheader(
        "🎯 Hiring Probability for Demanded Role"
    )

    demanded_roles = (
        demand_df["role"]
        .head(20)
        .tolist()
    )

    selected_role = st.selectbox(
        "Select a demanded role",
        demanded_roles
    )

    role_row = demand_df[
        demand_df["role"]
        == selected_role
    ].iloc[0]

    probability = calculate_hiring_probability(
        role_row
    )

    # ========================================================
    # PROBABILITY
    # ========================================================

    st.metric(
        "Estimated Hiring Activity Probability",
        f"{probability}%"
    )

    st.progress(
        probability / 100
    )

    # ========================================================
    # ROLE DETAILS
    # ========================================================

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Historical Job Posts",
            int(
                role_row[
                    "historical_posts"
                ]
            )
        )

    with c2:

        st.metric(
            "Companies Posting",
            int(
                role_row[
                    "historical_companies"
                ]
            )
        )

    with c3:

        st.metric(
            "Current Live Openings",
            int(
                role_row[
                    "current_openings"
                ]
            )
        )

    # ========================================================
    # ROLE SUMMARY
    # ========================================================

    st.markdown(
        f"""
        ### 🔎 {selected_role}

        **Demand score:** {role_row["demand_score"]:.1f}

        **Historical job-posting activity:**
        {int(role_row["historical_posts"]):,} postings

        **Companies posting this role:**
        {int(role_row["historical_companies"]):,}

        **Current live openings:**
        {int(role_row["current_openings"]):,}
        """
    )

    # ========================================================
    # DATA TABLE
    # ========================================================

    with st.expander(
        "View demanded roles data"
    ):

        display_df = demand_df[
            [
                "role",
                "historical_posts",
                "historical_companies",
                "current_openings",
                "demand_score"
            ]
        ].copy()

        display_df.columns = [
            "Role",
            "Historical Posts",
            "Companies Posting",
            "Current Openings",
            "Demand Score"
        ]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# STUDENT PORTAL COMPATIBILITY
# ============================================================

def future_hiring_page():
    show_future_hiring()