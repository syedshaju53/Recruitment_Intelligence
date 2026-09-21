# from pathlib import Path

# import pandas as pd
# import plotly.express as px
# import streamlit as st


# # ============================================================
# # PATHS
# # ============================================================

# BASE_DIR = Path(__file__).resolve().parent.parent
# DATA_DIR = BASE_DIR / "data"

# JOBS_FILE = DATA_DIR / "jobs.csv"
# HISTORY_FILE = DATA_DIR / "historical_recruitment.csv"
# COMPANIES_FILE = DATA_DIR / "companies.csv"


# # ============================================================
# # HELPERS
# # ============================================================

# def normalize_columns(df):
#     df.columns = (
#         df.columns
#         .astype(str)
#         .str.strip()
#         .str.lower()
#         .str.replace(" ", "_", regex=False)
#         .str.replace("-", "_", regex=False)
#     )

#     rename_map = {
#         "company": "company_name",
#         "companyname": "company_name",
#         "job_title": "role",
#         "job_role": "role",
#         "vacancy": "openings",
#         "vacancies": "openings",
#         "opening": "openings",
#         "job_openings": "openings",
#         "application_link": "application_url",
#         "apply_url": "application_url",
#     }

#     return df.rename(columns=rename_map)


# def normalize_text(value):
#     return str(value).strip().lower()


# def is_active_job(status):
#     return normalize_text(status) in {
#         "open",
#         "active",
#         "hiring",
#         "ongoing",
#     }


# # ============================================================
# # LOAD JOBS
# # ============================================================

# @st.cache_data
# def load_jobs():

#     try:
#         df = pd.read_csv(JOBS_FILE)
#         df = normalize_columns(df)

#         required = [
#             "company_name",
#             "role",
#             "department",
#             "month",
#             "openings",
#             "salary",
#             "location",
#             "status",
#             "application_url",
#         ]

#         for column in required:
#             if column not in df.columns:
#                 df[column] = ""

#         for column in [
#             "company_name",
#             "role",
#             "department",
#             "month",
#             "salary",
#             "location",
#             "status",
#             "application_url",
#         ]:
#             df[column] = (
#                 df[column]
#                 .fillna("")
#                 .astype(str)
#                 .str.strip()
#             )

#         df["openings"] = pd.to_numeric(
#             df["openings"],
#             errors="coerce"
#         ).fillna(0)

#         return df

#     except Exception as e:
#         st.error(f"Unable to load jobs.csv: {e}")
#         return pd.DataFrame()


# # ============================================================
# # LOAD HISTORICAL DATA
# # ============================================================

# @st.cache_data
# def load_history():

#     try:
#         df = pd.read_csv(HISTORY_FILE)

#         df.columns = (
#             df.columns
#             .astype(str)
#             .str.strip()
#             .str.lower()
#             .str.replace(" ", "_", regex=False)
#         )

#         required = [
#             "company",
#             "year",
#             "month",
#             "department",
#             "recruitment_count",
#         ]

#         for column in required:
#             if column not in df.columns:
#                 df[column] = ""

#         for column in [
#             "company",
#             "month",
#             "department",
#         ]:
#             df[column] = (
#                 df[column]
#                 .fillna("")
#                 .astype(str)
#                 .str.strip()
#             )

#         df["year"] = pd.to_numeric(
#             df["year"],
#             errors="coerce"
#         )

#         df["recruitment_count"] = pd.to_numeric(
#             df["recruitment_count"],
#             errors="coerce"
#         ).fillna(0)

#         return df

#     except Exception as e:
#         st.error(
#             f"Unable to load historical_recruitment.csv: {e}"
#         )
#         return pd.DataFrame()


# # ============================================================
# # LOAD COMPANY DATA
# # ============================================================

# @st.cache_data
# def load_companies():

#     try:
#         df = pd.read_csv(COMPANIES_FILE)
#         df = normalize_columns(df)

#         if "company_name" not in df.columns:

#             if "company" in df.columns:
#                 df["company_name"] = df["company"]

#             else:
#                 df["company_name"] = ""

#         return df

#     except Exception:
#         return pd.DataFrame()


# # ============================================================
# # GET ALL JOBS
# # ============================================================

# def get_all_jobs():

#     jobs = load_jobs().copy()

#     prototype_jobs = st.session_state.get(
#         "prototype_jobs",
#         []
#     )

#     if prototype_jobs:

#         recruiter_jobs = pd.DataFrame(
#             prototype_jobs
#         )

#         if not recruiter_jobs.empty:

#             recruiter_jobs = normalize_columns(
#                 recruiter_jobs
#             )

#             if (
#                 "company" in recruiter_jobs.columns
#                 and "company_name"
#                 not in recruiter_jobs.columns
#             ):
#                 recruiter_jobs["company_name"] = (
#                     recruiter_jobs["company"]
#                 )

#             required = [
#                 "company_name",
#                 "role",
#                 "department",
#                 "month",
#                 "openings",
#                 "salary",
#                 "location",
#                 "status",
#                 "application_url",
#             ]

#             for column in required:
#                 if column not in recruiter_jobs.columns:
#                     recruiter_jobs[column] = ""

#             recruiter_jobs["openings"] = pd.to_numeric(
#                 recruiter_jobs["openings"],
#                 errors="coerce"
#             ).fillna(0)

#             recruiter_jobs = recruiter_jobs[
#                 required
#             ]

#             jobs = pd.concat(
#                 [jobs, recruiter_jobs],
#                 ignore_index=True
#             )

#     # Final safety check
#     if "openings" not in jobs.columns:
#         jobs["openings"] = 0

#     jobs["openings"] = pd.to_numeric(
#         jobs["openings"],
#         errors="coerce"
#     ).fillna(0)

#     return jobs


# # ============================================================
# # COMPANY PAGE
# # ============================================================

# def show_company_profile(
#     company,
#     jobs_df,
#     history_df
# ):

#     st.markdown(
#         f"## 🏢 {company}"
#     )

#     company_jobs = jobs_df[
#         jobs_df["company_name"]
#         .apply(normalize_text)
#         == normalize_text(company)
#     ].copy()

#     company_active_jobs = company_jobs[
#         company_jobs["status"]
#         .apply(is_active_job)
#     ].copy()

#     company_history = history_df[
#         history_df["company"]
#         .apply(normalize_text)
#         == normalize_text(company)
#     ].copy()

#     # ========================================================
#     # OVERVIEW METRICS
#     # ========================================================

#     total_openings = int(
#         company_active_jobs["openings"].sum()
#     )

#     active_roles = (
#         company_active_jobs["role"]
#         .nunique()
#     )

#     departments = (
#         company_active_jobs["department"]
#         .nunique()
#     )

#     locations = (
#         company_active_jobs["location"]
#         .nunique()
#     )

#     col1, col2, col3, col4 = st.columns(4)

#     with col1:
#         st.metric(
#             "Current Openings",
#             f"{total_openings:,}"
#         )

#     with col2:
#         st.metric(
#             "Active Roles",
#             active_roles
#         )

#     with col3:
#         st.metric(
#             "Departments",
#             departments
#         )

#     with col4:
#         st.metric(
#             "Locations",
#             locations
#         )

#     # ========================================================
#     # CURRENT JOBS
#     # ========================================================

#     st.divider()

#     st.subheader(
#         "💼 Current Job Openings"
#     )

#     if company_active_jobs.empty:

#         st.info(
#             "This company currently has no active jobs."
#         )

#     else:

#         company_active_jobs = (
#             company_active_jobs
#             .sort_values(
#                 "openings",
#                 ascending=False
#             )
#         )

#         for _, job in company_active_jobs.iterrows():

#             with st.container(border=True):

#                 col1, col2 = st.columns(
#                     [4, 1]
#                 )

#                 with col1:

#                     st.markdown(
#                         f"### 💼 {job['role']}"
#                     )

#                     st.write(
#                         f"🎓 Department: "
#                         f"{job['department']}"
#                     )

#                     st.write(
#                         f"📍 Location: "
#                         f"{job['location']}"
#                     )

#                     st.write(
#                         f"💰 Salary: "
#                         f"{job['salary']}"
#                     )

#                     st.write(
#                         f"📅 Hiring Month: "
#                         f"{job['month']}"
#                     )

#                 with col2:

#                     st.metric(
#                         "Openings",
#                         int(job["openings"])
#                     )

#                     url = str(
#                         job["application_url"]
#                     ).strip()

#                     if (
#                         url
#                         and url.lower() != "nan"
#                     ):

#                         st.link_button(
#                             "Apply Now",
#                             url,
#                             width="stretch"
#                         )

#     # ========================================================
#     # HISTORICAL RECRUITMENT
#     # ========================================================

#     st.divider()

#     st.subheader(
#         "📊 Historical Recruitment"
#     )

#     if company_history.empty:

#         st.info(
#             "No historical recruitment data available."
#         )

#     else:

#         total_historical = int(
#             company_history[
#                 "recruitment_count"
#             ].sum()
#         )

#         latest_year = (
#             company_history["year"]
#             .dropna()
#             .max()
#         )

#         col1, col2 = st.columns(2)

#         with col1:

#             st.metric(
#                 "Total Historical Recruitment",
#                 f"{total_historical:,}"
#             )

#         with col2:

#             if pd.notna(latest_year):

#                 latest_count = int(
#                     company_history[
#                         company_history["year"]
#                         == latest_year
#                     ]["recruitment_count"]
#                     .sum()
#                 )

#                 st.metric(
#                     f"Recruitment in {int(latest_year)}",
#                     f"{latest_count:,}"
#                 )

#         # ----------------------------------------------------
#         # YEARLY TREND
#         # ----------------------------------------------------

#         yearly = (
#             company_history
#             .groupby(
#                 "year",
#                 as_index=False
#             )["recruitment_count"]
#             .sum()
#         )

#         yearly = yearly.dropna(
#             subset=["year"]
#         )

#         if not yearly.empty:

#             yearly["year"] = (
#                 yearly["year"]
#                 .astype(int)
#             )

#             fig = px.line(
#                 yearly,
#                 x="year",
#                 y="recruitment_count",
#                 markers=True,
#                 title=f"{company} — Yearly Recruitment"
#             )

#             fig.update_layout(
#                 xaxis_title="Year",
#                 yaxis_title="Recruitment Count"
#             )

#             st.plotly_chart(
#                 fig,
#                 width="stretch"
#             )

#     # ========================================================
#     # DEPARTMENT-WISE HIRING
#     # ========================================================

#     st.divider()

#     st.subheader(
#         "🎯 Department-wise Recruitment"
#     )

#     if not company_history.empty:

#         department_data = (
#             company_history
#             .groupby(
#                 "department",
#                 as_index=False
#             )["recruitment_count"]
#             .sum()
#             .sort_values(
#                 "recruitment_count",
#                 ascending=False
#             )
#         )

#         if not department_data.empty:

#             fig = px.bar(
#                 department_data,
#                 x="department",
#                 y="recruitment_count",
#                 title=f"{company} — Department-wise Hiring"
#             )

#             fig.update_layout(
#                 xaxis_title="Department",
#                 yaxis_title="Recruitment Count"
#             )

#             st.plotly_chart(
#                 fig,
#                 width="stretch"
#             )

#     # ========================================================
#     # MONTHLY HIRING
#     # ========================================================

#     st.subheader(
#         "📅 Monthly Hiring Pattern"
#     )

#     if not company_history.empty:

#         monthly = (
#             company_history
#             .groupby(
#                 "month",
#                 as_index=False
#             )["recruitment_count"]
#             .sum()
#             .sort_values(
#                 "recruitment_count",
#                 ascending=False
#             )
#         )

#         if not monthly.empty:

#             fig = px.bar(
#                 monthly,
#                 x="month",
#                 y="recruitment_count",
#                 title=f"{company} — Monthly Hiring Pattern"
#             )

#             fig.update_layout(
#                 xaxis_title="Month",
#                 yaxis_title="Recruitment Count"
#             )

#             st.plotly_chart(
#                 fig,
#                 width="stretch"
#             )

#     # ========================================================
#     # ROLE ANALYSIS
#     # ========================================================

#     st.divider()

#     st.subheader(
#         "💼 Roles Currently Hiring"
#     )

#     if company_active_jobs.empty:

#         st.info(
#             "No active roles available."
#         )

#     else:

#         role_df = (
#             company_active_jobs[
#                 [
#                     "role",
#                     "department",
#                     "openings",
#                     "location",
#                     "salary"
#                 ]
#             ]
#             .sort_values(
#                 "openings",
#                 ascending=False
#             )
#         )

#         role_df.columns = [
#             "Role",
#             "Department",
#             "Openings",
#             "Location",
#             "Salary"
#         ]

#         st.dataframe(
#             role_df,
#             width="stretch",
#             hide_index=True
#         )

#     # ========================================================
#     # PROTOTYPE INTELLIGENCE
#     # ========================================================

#     st.divider()

#     st.subheader(
#         "🤖 Recruitment Intelligence"
#     )

#     if not company_active_jobs.empty:

#         max_openings = max(
#             int(company_active_jobs["openings"].max()),
#             1
#         )

#         historical_total = int(
#             company_history[
#                 "recruitment_count"
#             ].sum()
#         ) if not company_history.empty else 0

#         max_history = max(
#             int(
#                 history_df[
#                     "recruitment_count"
#                 ].max()
#             ) if not history_df.empty else 1,
#             1
#         )

#         opening_score = (
#             total_openings / max_openings
#         )

#         history_score = (
#             historical_total / max_history
#         )

#         probability = round(
#             min(
#                 (
#                     opening_score * 0.60
#                     + history_score * 0.40
#                 ) * 100,
#                 99
#             ),
#             1
#         )

#         st.metric(
#             "Prototype Hiring Probability",
#             f"{probability}%"
#         )

#         st.caption(
#             "Prototype score based on current openings "
#             "and historical recruitment. This will be "
#             "replaced by the actual ML model later."
#         )


# # ============================================================
# # MAIN FUNCTION
# # ============================================================

# def show_company_intelligence():

#     st.title(
#         "🏢 Company Intelligence"
#     )

#     st.markdown(
#         """
#         Explore detailed recruitment intelligence for
#         individual companies, including current openings,
#         recruitment history, hiring patterns and roles.
#         """
#     )

#     st.divider()

#     jobs_df = get_all_jobs()
#     history_df = load_history()

#     if jobs_df.empty:

#         st.warning(
#             "No job data available."
#         )

#         return

#     # ========================================================
#     # COMPANY LIST
#     # ========================================================

#     companies = sorted(
#         [
#             str(company)
#             for company in
#             jobs_df["company_name"]
#             .dropna()
#             .unique()
#             if str(company).strip()
#         ]
#     )

#     if not companies:

#         st.warning(
#             "No companies found."
#         )

#         return

#     selected_company = st.selectbox(
#         "🏢 Select Company",
#         companies
#     )

#     st.divider()

#     show_company_profile(
#         selected_company,
#         jobs_df,
#         history_df
#     )